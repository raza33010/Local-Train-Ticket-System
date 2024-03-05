# @app.route('/add_class', methods=['POST'])
# def add_class():
#     form = CenterForm(request.form)
#     if not form.validate():
#         for field, errors in form.errors.items():
#             for error in errors:
#                 flash(f"{field}: {error}", "error")
#         return jsonify(success=False, errors=form.errors)
#     ...