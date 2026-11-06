# routes/admin.py
# CRUD kriteria, dashboard, export.
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from models import HasilPenilaian, db, Kriteria, Pengajuan, User, AuditLog, Pengaturan
from routes.auth import role_required
import io
from openpyxl import Workbook

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total = Pengajuan.query.count()
    per_status = {s: Pengajuan.query.filter_by(status=s).count()
                  for s in ['menunggu', 'disetujui', 'ditolak', 'perbaikan', 'banding']}
    layak = per_status.get('disetujui', 0)
    persen_layak = (layak / total * 100) if total else 0
    return render_template('admin/dashboard.html', total=total,
                           per_status=per_status, persen_layak=round(persen_layak, 1))


@admin_bp.route('/admin/kriteria', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def kriteria():
    if request.method == 'POST':
        # Update bobot & tipe dari form
        for k in Kriteria.query.all():
            k.bobot = float(request.form.get(f'bobot_{k.id}', k.bobot))
            k.tipe = request.form.get(f'tipe_{k.id}', k.tipe)
        # Validasi total bobot = 1
        total = sum(k.bobot for k in Kriteria.query.all())
        if abs(total - 1.0) > 0.001:
            flash(f'Total bobot harus 1.0 (sekarang {total:.2f}). Perubahan dibatalkan.')
            db.session.rollback()
        else:
            db.session.add(AuditLog(user_id=current_user.id, aksi='ubah kriteria'))
            db.session.commit()
            flash('Kriteria diperbarui')
        return redirect(url_for('admin.kriteria'))
    daftar = Kriteria.query.all()
    return render_template('admin/kriteria.html', daftar=daftar)


@admin_bp.route('/admin/export/excel')
@login_required
@role_required('admin')
def export_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = 'Pengajuan'
    ws.append(['ID', 'NIK', 'Nama', 'Penghasilan', 'Tanggungan', 'Status'])
    for p in Pengajuan.query.all():
        ws.append([p.id, p.nik, p.nama, p.penghasilan, p.tanggungan, p.status])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name='laporan_pengajuan.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@admin_bp.route('/admin/audit')
@login_required
@role_required('admin')
def audit():
    logs = AuditLog.query.order_by(AuditLog.waktu.desc()).limit(200).all()
    return render_template('admin/audit.html', logs=logs)

# routes/admin.py (Tambahkan di bagian paling bawah)

@admin_bp.route('/peringkat-bantuan')
@login_required
def peringkat_bantuan():
    # Cek manual: Hanya Admin dan Staf yang boleh masuk
    if current_user.role not in ['admin', 'staf']:
        abort(403)
        
    # Ambil data gabungan, urutkan dari skor SAW tertinggi
    daftar_peringkat = db.session.query(HasilPenilaian, Pengajuan)\
        .join(Pengajuan, HasilPenilaian.pengajuan_id == Pengajuan.id)\
        .order_by(HasilPenilaian.skor_saw.desc())\
        .all()
        
    return render_template('peringkat.html', daftar=daftar_peringkat)