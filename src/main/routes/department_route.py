from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g

dept_bp = Blueprint("department", __name__, url_prefix='/department')


@dept_bp.route("/", methods=['GET', 'POST'])
def index():
    return "department"
