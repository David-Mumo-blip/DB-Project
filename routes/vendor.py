from flask import Blueprint, render_template, request, redirect, url_for, flash
vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')