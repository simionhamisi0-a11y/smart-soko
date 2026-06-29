from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATIONS ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_soko'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'smart_soko_siri_yetu_kali'  # Siri ya kulinda session
db = SQLAlchemy(app)


# --- 1. TABLE YA WATUMIAJI (USERS) ---
class watumiaji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
# Tutaweka 'admin' au 'wakala'. Kimasanduku inakuwa 'wakala' mtu akisajili
    role = db.Column(db.String(20), nullable=False, default='wakala')

# --- 2. TABLE YA BEI ZA MAZAO ---
class bei_za_mazao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(100), nullable=False)
    soko_location = db.Column(db.String(100), nullable=False)
    zao_name = db.Column(db.String(100), nullable=False)
    bei_ya_jumla = db.Column(db.Float, nullable=False)
    kipimo = db.Column(db.String(50), nullable=False)
    hali_ya_soko = db.Column(db.String(50), nullable=False)
    tarehe_iliyoingizwa = db.Column(db.String(50), nullable=False)
    # Hapa: 'pending' (inasubiri), 'approved' (imekubaliwa), au 'rejected' (imegaliwa)
    status = db.Column(db.String(20), nullable=False, default='pending')


# --- 3. ROUTE KUU (INDEX PAGE) ---
@app.route('/')
def index():
    try:
        # Inavuta data zote na kuzipanga kuanzia mpya hadi ya zamani
        zote = bei_za_mazao.query.order_by(bei_za_mazao.id.desc()).all()

        # 2. Piga hesabu za Kadi za Dashboard
        # Kadi ya 1: Jumla ya data zilizohakikiwa (Approved)
        jumla_approved = bei_za_mazao.query.filter_by(status='approved').count()
        
        # Kadi ya 2: Idadi ya data zinazosubiri uhakiki (Pending)
        jumla_pending = bei_za_mazao.query.filter_by(status='pending').count()
        
        # Kadi ya 3: Bei ya juu kabisa iliyoingizwa sokoni
        max_bei_record = bei_za_mazao.query.order_by(bei_za_mazao.bei_ya_jumla.desc()).first()
        bei_ya_juu = max_bei_record.bei_ya_jumla if max_bei_record else 0
        zao_la_juu = max_bei_record.zao_name if max_bei_record else "Hakuna"
        
        # Kadi ya 4: Idadi ya mawakala wa kipekee (Unique Agents)
        # Hapa tunatumia db.distinct kuhesabu mawakala bila kurudia majina
        mawakala_distinct = db.session.query(bei_za_mazao.agent_name).distinct().count()
        
        # Tunatuma hizi data zote kwenda kwenye HTML
        return render_template('index.html', 
                               bei_za_mazao=zote, 
                               session=session,
                               kadi_approved=jumla_approved,
                               kadi_pending=jumla_pending,
                               kadi_bei_juu=bei_ya_juu,
                               kadi_zao_juu=zao_la_juu,
                               kadi_mawakala=mawakala_distinct)
    
    except Exception as e:
        return f"Imefeli kusoma data kutoka MySQL: {e}"


# --- 4. ROUTE YA USAJILI (REGISTER) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        mtumiaji_tayari = watumiaji.query.filter_by(username=username).first()
        if mtumiaji_tayari:
            return "Jina hili limeshatumika! Chagua lingine."
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        mtumiaji_mpya = watumiaji(username=username, password=hashed_password)
        
        db.session.add(mtumiaji_mpya)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        mtumiaji = watumiaji.query.filter_by(username=username).first()
        
        if mtumiaji and check_password_hash(mtumiaji.password, password):
            session['user_id'] = mtumiaji.id
            session['username'] = mtumiaji.username
            session['role'] = mtumiaji.role # <--- Hii ni muhimu sana!
            return redirect(url_for('index'))
        else:
            return "Username au Password sio sahihi!"
            
    return render_template('login.html')


# --- 6. ROUTE YA LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# --- 7. ROUTE YA KUINGIZA DATA (SUBMIT) ---
@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return "Samahani! Lazima uingie (Login) kwanza ili kuingiza data."

    if request.method == 'POST':
        try:
            bei_input = float(request.form['bei_ya_jumla'])
            if bei_input <= 0:
                return "Makosa: Bei ya jumla lazima iwe kubwa kuliko 0!"

            taarifa_mpya = bei_za_mazao(
                agent_name=session['username'],  # Jina linatoka kwenye login moja kwa moja
                soko_location=request.form['soko_location'],
                zao_name=request.form['zao_name'],
                bei_ya_jumla=bei_input,
                kipimo=request.form['kipimo'],
                hali_ya_soko=request.form['hali_ya_soko'],
                tarehe_iliyoingizwa=request.form['tarehe_iliyoingizwa']
            )

            db.session.add(taarifa_mpya)
            db.session.commit()
            return redirect(url_for('index'))
            
        except Exception as e:
            return f"Data haijaingia! Tatizo: {e}"


# --- ROUTE YA KUFUTA (ADMIN TU) ---
@app.route('/delete/<int:id>')
def delete(id):
    # Kagua kama ameingia NA kama yeye ni Admin
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Samahani! Huna mamlaka ya kufuta taarifa. Hii ni kazi ya Admin tu!"
    try:
        record_ya_kufuta = bei_za_mazao.query.get_or_404(id)
        db.session.delete(record_ya_kufuta)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Imefeli: {e}"

# --- ROUTE YA KUFUNGUA UKURASA WA EDIT (ADMIN TU) ---
@app.route('/edit/<int:id>')
def edit(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Samahani! Huwezi kubadilisha data. Wasiliana na Admin mkuu."
    try:
        bidhaa = bei_za_mazao.query.get_or_404(id)
        return render_template('edit.html', b=bidhaa)
    except Exception as e:
        return f"Imefeli: {e}"
    
@app.route('/approve/<int:id>')
def approve(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Huna ruhusa hii!"
    try:
        data = bei_za_mazao.query.get_or_404(id)
        data.status = 'approved' # Imepitishwa na admin
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Imeshindikana kuidhinisha: {e}"


# --- 10. ROUTE YA KUHIFADHI MABADILIKO (UPDATE) ---
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    if 'user_id' not in session:
        return "Samahani! Huna ruhusa ya kubadilisha taarifa hii."
        
    if request.method == 'POST':
        try:
            bidhaa = bei_za_mazao.query.get_or_404(id)
            
            bei_input = float(request.form['bei_ya_jumla'])
            if bei_input <= 0:
                return "Makosa: Bei mpya lazima iwe kubwa kuliko 0!"

            bidhaa.agent_name = session['username']
            bidhaa.soko_location = request.form['soko_location']
            bidhaa.zao_name = request.form['zao_name']
            bidhaa.bei_ya_jumla = bei_input
            bidhaa.kipimo = request.form['kipimo']
            bidhaa.hali_ya_soko = request.form['hali_ya_soko']
            bidhaa.tarehe_iliyoingizwa = request.form['tarehe_iliyoingizwa']

            db.session.commit()
            return redirect(url_for('index'))
            
        except ValueError:
            return "Makosa: Ingiza namba halali kwenye bei!"
        except Exception as e:
            return f"Mabadiliko hayajafanikiwa! Tatizo: {e}"


# --- INATENGENEZA TABLE KIOTOMATIKI ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    import os
    # Hii inaruhusu seva ya mtandaoni kupanga port yenyewe, isipopo weka 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) #