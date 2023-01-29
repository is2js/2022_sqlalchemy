from flask import Blueprint, render_template

from src.infra.tutorial3 import Department

dept_bp = Blueprint("department", __name__, url_prefix='/department')


@dept_bp.route("/organization", methods=['GET'])
def organization():
    tree = Department.get_all_tree()

    return render_template('department/organization.html',
                           tree=tree
                           )


@dept_bp.route("/management", methods=['GET'])
def management():

    return render_template('department/component_test.html')

@dept_bp.route("/test2", methods=['GET'])
def test2():

    return render_template('department/component_test2.html')
