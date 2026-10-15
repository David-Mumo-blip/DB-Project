from flask import Blueprint, render_template, request, redirect, url_for, flash
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')