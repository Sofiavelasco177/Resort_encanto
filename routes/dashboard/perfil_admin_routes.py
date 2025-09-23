"""@admin_bp.route('/perfil_admin', methods=['GET', 'POST'])
def perfil_admin():
    # Suponiendo que el admin está logueado y su id está en session['user']['id']
    usuario_id = session.get('user', {}).get('id')
    usuario = Usuario.query.get(usuario_id)
    perfil = PerfilAdmin.query.filter_by(usuario_id=usuario_id).first()
    if request.method == 'POST':
        # Actualizar o crear perfil
        if not perfil:
            perfil = PerfilAdmin(usuario_id=usuario_id)
            db.session.add(perfil)
        perfil.cargo = request.form['cargo']
        perfil.area = request.form['area']
        perfil.division = request.form['division']
        perfil.empresa = request.form['empresa']
        perfil.supervisor = request.form['supervisor']
        perfil.suplente = request.form['suplente']
        perfil.tipo_contrato = request.form['tipo_contrato']
        perfil.fecha_ingreso = request.form['fecha_ingreso']
        db.session.commit()
        flash('Datos actualizados correctamente', 'success')
        return redirect(url_for('admin.perfil_admin'))
    return render_template('dashboard/perfil_admin.html', usuario=usuario, perfil=perfil)
    return redirect(url_for("admin.admin_restaurante"))"""