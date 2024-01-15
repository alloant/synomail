#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request
from flask_login import login_required, current_user

from app.docs.documentation import documentation_view

bp = Blueprint('docs', __name__)

@bp.route('/documentation')
@login_required
def documentation():
    return documentation_view(request.args)

