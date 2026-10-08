from flask import Blueprint, render_template, request, redirect, url_for, flash
student_bp = Blueprint('student', __name__, url_prefix='/student')