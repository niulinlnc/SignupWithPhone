# -*- coding: utf-8 -*-
import logging
from openerp import http , _
from openerp.http import request
import re
import werkzeug
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type , NumberParseException
from openerp import tools
from openerp.addons.web.controllers.main import ensure_db, Home
from openerp.addons.auth_signup.res_users import SignupError

_logger = logging.getLogger(__name__)

class AuthSignupHome(Home):
    
    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        """ Override router to add Email/Mobile Validation.
        """
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                return super(AuthSignupHome, self).web_login(*args, **kw)
            except (SignupError, AssertionError), e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("This User is Already Exists.")
                else:
#                     Raise Error for Email/Mobile not available.
                    if not qcontext['login'] and not qcontext['mobile']:
                        _logger.error(e.message)
                        qcontext['error'] = _("Please Enter Email or Mobile.")
                    if qcontext['password'] != qcontext['confirm_password']:
                        _logger.error(e.message)
                        qcontext['error'] = _("Please Enter Same Password.")
         
        return request.render('auth_signup.signup', qcontext)

    def get_auth_signup_qcontext(self):
        """ Shared helper returning the rendering context for signup and reset password.
            Check Condition If Email not Exists, then Signup with Mobile.
        """
        if request.params.items() and request.params['mobile']:
            try:
                carrier._is_mobile(number_type(phonenumbers.parse(request.params['mobile'])))
            except NumberParseException:
                request.params['error'] = _("Please Enter Valid Mobile Number")
        if request.params.items() and request.params['login']:
            if not tools.single_email_re.match(request.params['login']):
                request.params['error'] = _("Please Enter Valid Email")        
        if request.params.items() and request.params['mobile'] and request.params['login'] == '':
            request.params['login'] = request.params['mobile']
        qcontext = request.params.copy()
        qcontext.update(self.get_auth_signup_config())
        if qcontext.get('token'):
            try:
                # retrieve the user info (name, login or email) corresponding to a signup token
                token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
                for k, v in token_infos.items():
                    qcontext.setdefault(k, v)
            except:
                qcontext['error'] = _("Invalid signup token")
                qcontext['invalid_token'] = True
        return qcontext
    
    def do_signup(self, qcontext):
        """ Override do_signup for Create User & Partner with Extra field Mobile.
        """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password','mobile') }
        assert values.get('password') == qcontext.get('confirm_password'), "Passwords do not match; please retype them."
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()