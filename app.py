from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
import os
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
LOGO_PATH = 'static/logo.jpg'  # your logo
EXCEL_FILE = 'students.xlsx'
BACKGROUND_PATH = 'static/bg.png'  # background image for PDF
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure Excel file exists
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=[
        'id_number','name','christanity_name','entry_date','type','class','department','field','experience','company',
        'emergency_name','emergency_phone','father_status','father_name','father_phone','father_place','fathers_name',
        'phone','gender','age','birth_date','mother_name','address','house_number','wereda','kebele','city','marital_status','volunteer','photo'
    ])
    df.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def home():
    return render_template('layout.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data = request.form.to_dict()
        data['id_number'] = data['id_number'].strip()  # remove spaces

        # Load existing students and clean IDs
        df = pd.read_excel(EXCEL_FILE)
        df['id_number'] = df['id_number'].astype(str).str.strip()

        # Check for duplicate ID
        if data['id_number'] in df['id_number'].values:
            flash("ይህ መለያ ቁጥር አስቀድሞ መመዝገብ አለበት!", "danger")
            return redirect(url_for('register'))

        # Handle photo
        photo = request.files.get('photo')
        filename = ''
        if photo and photo.filename != '':
            filename = data['id_number'] + '_' + photo.filename
            photo.save(os.path.join(UPLOAD_FOLDER, filename))
        data['photo'] = filename

        # Ensure volunteer is a list and limit to 3
        data['volunteer'] = request.form.getlist('volunteer[]')
        if len(data['volunteer']) > 3:
            flash("ከ3 ብቻ የሚምረጡ!", "danger")
            return redirect(url_for('register'))

        # Save to Excel
        new_df = pd.DataFrame([data])
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

        flash("በተሳካ ሁኔታ ተመዝግበዋል!", "success")
        return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/admin', methods=['GET'])
def admin():
    df = pd.read_excel(EXCEL_FILE)
    df['volunteer'] = df['volunteer'].apply(lambda x: eval(x) if isinstance(x,str) else x)
    students = df.to_dict(orient='records')
    return render_template('admin.html', students=students)


@app.route('/admin/search', methods=['POST'])
def admin_search():
    query = request.form.get("search_id", "").strip()
    df = pd.read_excel(EXCEL_FILE)
    df['volunteer'] = df['volunteer'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    students = df.to_dict(orient='records')

    if not query:
        flash("እባክዎ ስም ወይም መለያ ቁጥር ያስገቡ።", "warning")
        return render_template("admin.html", students=students)

    results = [
        s for s in students
        if str(s.get("id_number", "")).strip() == query
        or query.lower() in str(s.get("name", "")).lower()
    ]

    if not results:
        flash("ምንም ተማሪ አልተገኘም።", "danger")
        return render_template("admin.html", students=students)

    return render_template("admin.html", students=results)


@app.route('/admin/delete/<student_id>', methods=['POST'])
def delete_student(student_id):
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df['id_number'] = df['id_number'].astype(str).str.strip()
        if student_id in df['id_number'].values:
            # Delete student
            df = df[df['id_number'] != student_id]
            df.to_excel(EXCEL_FILE, index=False)
            flash("Student deleted successfully", "success")
        else:
            flash("Student not found", "danger")
    else:
        flash("No student data found", "danger")
    return redirect(url_for('admin'))


@app.route('/students')
def students():
    if not os.path.exists(EXCEL_FILE):
        students = []
    else:
        df = pd.read_excel(EXCEL_FILE)
        df['volunteer'] = df['volunteer'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        students = df.to_dict(orient='records')
    return render_template('students.html', students=students)


@app.route('/generate_pdf/<student_id>')
def generate_pdf(student_id):
    df = pd.read_excel(EXCEL_FILE)
    df['volunteer'] = df['volunteer'].apply(lambda x: eval(x) if isinstance(x,str) else x)
    student = df[df['id_number'].astype(str) == student_id]

    if student.empty:
        return "Student not found"

    student = student.iloc[0]
    pdf = FPDF()
    pdf.add_page()

    # Add background image
    if os.path.exists(BACKGROUND_PATH):
        pdf.image(BACKGROUND_PATH, x=0, y=0, w=210, h=297)

    # Register Amharic font
    pdf.add_font("AbyssinicaSIL","", "static/AbyssinicaSIL-Regular.ttf", uni=True)
    pdf.add_font("AbyssinicaSIL","B", "static/AbyssinicaSIL-Regular.ttf", uni=True)

    pdf.set_font("AbyssinicaSIL", "B", 16)
    pdf.cell(0, 15, "የተማሪ መረጃ", ln=True, align='C')
    pdf.ln(5)

    # Logo
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=8, w=30)

    # Photo
    if student['photo'] and os.path.exists(os.path.join(UPLOAD_FOLDER, student['photo'])):
        pdf.image(os.path.join(UPLOAD_FOLDER, student['photo']), x=160, y=8, w=30)

    # Helper function for two-column layout
    def write_two_columns(fields, labels):
        col_width = 120
        x_start = pdf.get_x()
        count = 0
        for field in fields:
            value = student.get(field, '-') or '-'
            label = labels.get(field, field)
            text = f"{label} {value}" if not isinstance(value, list) else f"{label} {'፣ '.join(value)}"
            pdf.set_x(x_start if count % 2 == 0 else x_start + col_width)
            pdf.set_font("AbyssinicaSIL","",12)
            pdf.cell(col_width, 8, text, ln=0)
            if count % 2 == 1:
                pdf.ln(8)
            count += 1
        if count % 2 == 1:
            pdf.ln(15)
        pdf.ln(6)

    # Labels
    personal_labels = {
        'id_number': 'የአባል መለያ ቁጥር፡',
        'name': 'የአባል ሙሉ ስም፡',
        'christanity_name': 'የክርስትና ስም፡',
        'type': 'ዓይነት፡',
        'class': 'ክፍል፡',
        'gender': 'ፆታ፡',
        'age': 'እድሜ፡',
        'birth_date': 'የትውልድ ቀን፡',
        'phone': 'የአባሉ ስልክ ቁጥር፡',
        'address': 'አድራሻ፡',
        'house_number': 'የቤት ቁጥር፡',
        'wereda': 'ወረዳ፡',
        'kebele': 'ቀበሌ፡',
        'city': 'ከተማ፡',
        'marital_status': 'የጋብቻ ሁኔታ፡',
        'entry_date': 'የመግቢያ ቀን፡'
    }

    family_labels = {
        'mother_name': 'የእናት ሙሉ ስም፡',
        'fathers_name': 'የአባት ሙሉ ስም፡',
        'emergency_name': 'የአደጋ ጊዜ ተጠሪ ስም፡',
        'emergency_phone': 'የአደጋ ጊዜ ተጠሪ ስልክ፡',
        'father_status': 'የንስሀ የአባት ሁኔታ፡',
        'father_name': 'የንስሀ የአባት ስም፡',
        'father_phone': 'የንስሀ የአባት ስልክ፡',
        'father_place': 'የንስሀ የአባት የሚያገለግሉበት፡'
    }

    education_labels = {
        'type': 'ተማሪ/ሰራተኛ፡',
        'class': 'የክፍል ደረጃ፡',
        'department': 'የትምህርት ዘርፍ፡',
        'field': 'የስራ ዘርፍ፡',
        'experience': 'የስራ ልምድ፡',
        'company': 'የመስሪያ ቤት ስም፡'
    }

    volunteer_labels = {'volunteer': 'ምርጫዎች፡'}

    # Personal Info
    pdf.set_font("AbyssinicaSIL","B",14)
    pdf.cell(0, 12, "የግል መረጃ", ln=True, align='C')
    personal_fields = ['id_number','name', 'christanity_name','type','class','gender','age','birth_date',
                       'phone','address','house_number','wereda','kebele','city','marital_status','entry_date']
    write_two_columns(personal_fields, personal_labels)

    # Family Info
    pdf.set_font("AbyssinicaSIL","B",14)
    pdf.cell(0, 12, "የቤተሰብ መረጃ", ln=True, align='C')
    family_fields = ['mother_name','fathers_name','emergency_name','emergency_phone','father_status', 'father_name','father_phone','father_place']
    write_two_columns(family_fields, family_labels)

    # Education Info
    pdf.set_font("AbyssinicaSIL","B",14)
    pdf.cell(0, 12, "የትምህርት መረጃ", ln=True, align='C')
    education_fields = ['type','class','department','field','experience','company']
    write_two_columns(education_fields, education_labels)

    # Volunteer
    pdf.set_font("AbyssinicaSIL","B",14)
    pdf.cell(0, 12, "ማገልገል የሚፈልጉበት ክፍል", ln=True, align='C')
    volunteer = student.get('volunteer', [])
    if isinstance(volunteer, list):
        pdf.set_font("AbyssinicaSIL","",12)
        pdf.multi_cell(0, 8, "፣ ".join(volunteer))

    pdf_file = f"static/{student_id}.pdf"
    pdf.output(pdf_file)
    return send_file(pdf_file, as_attachment=True)

