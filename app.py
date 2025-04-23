from flask import Flask, render_template, request, redirect, session
import markdown
from db_config import get_connection

app = Flask(__name__, template_folder='templates')
app.secret_key = 'secret-key'

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM answers WHERE student_email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['student_id'] = user['id']
            return redirect('/survey')
        else:
            return redirect("https://docs.google.com/forms/d/1ekhJGNBZW6dl1wFjEw-O8vMW4qaDTm9CF-tmQVycakQ/edit?ts=67f49fa8")
    return render_template('login.html')

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'student_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    student_id = session['student_id']

    if request.method == 'POST':
        for i in range(1, 8):
            qid = request.form.get(f'question_id_{i}')
            pre = request.form.get(f'pre_score_{i}')
            post = request.form.get(f'post_score_{i}')
            # adding 5th rank
            ranks = [request.form.get(f'rank_{j}_{i}') for j in range(1, 6)]

            cursor.execute("""
                INSERT INTO llm_feedback (student_id, question_id, initial_understanding,
                    llm_default_rank, llm_skills_rank, llm_hobbies_rank, llm_subjects_rank,
                    llm_all_rank,final_understanding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, qid, pre, *ranks, post))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/thankyou')

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    cursor.execute("SELECT * FROM llm_response_default")
    default_responses = {row['question_id']: markdown.markdown(row['response']) for row in cursor.fetchall()}

    cursor.execute("SELECT * FROM llm_response_skills WHERE student_id = %s", (student_id,))
    skills = cursor.fetchone()

    cursor.execute("SELECT * FROM llm_response_hobbies WHERE student_id = %s", (student_id,))
    hobbies = cursor.fetchone()

    cursor.execute("SELECT * FROM llm_response_subjects WHERE student_id = %s", (student_id,))
    subjects = cursor.fetchone()

    # Fetch data from the new llm_response_all table
    cursor.execute("SELECT * FROM llm_response_all WHERE student_id = %s", (student_id,))
    all_responses_data = cursor.fetchone()

    

    topic_fields = [
        'java_response',
        'sql_response',
        'data_mining_response',
        'IOT_response',
        'HCI_response',
        'blockchains_response',
        'coding_response',
    ]

    all_responses = []
    for i, q in enumerate(questions):
        qid = q['question_id']
        # Add a safety check for the index
        topic_field = topic_fields[i] if i < len(topic_fields) else None
        response = {
            'question': q['question'] if 'question' in q else q.get('qusetion', ''),
            'question_id': qid,
            'default': default_responses.get(qid, ''),
            'skills': markdown.markdown(skills[topic_fields[i]]) if skills else '',
            'hobbies': markdown.markdown(hobbies[topic_fields[i]]) if hobbies else '',
            'subjects': markdown.markdown(subjects[topic_fields[i]]) if subjects else '',
            # Added the response from the new table
            'all': markdown.markdown(all_responses_data[topic_fields[i]]) if all_responses_data else ''
        }
        all_responses.append(response)

    cursor.close()
    conn.close()

    return render_template('survey.html', responses=all_responses)

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)