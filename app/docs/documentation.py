#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template

def documentation_view(args):
    topic = args.get('topic')

    match topic:
        case 'cr':
            return render_template('docs/docs_cr.html')
        case 'cl':
            return render_template('docs/docs_cl.html')
        case 'des':
            return render_template('docs/docs_des.html')
        case 'scr':
            return render_template('docs/docs_scr.html')
        case _:
            return render_template('docs/main.html')

