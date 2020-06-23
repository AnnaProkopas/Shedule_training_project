from flask import render_template, flash, redirect, url_for, request
from app import app, conn, is_admin
import os
from datetime import datetime, timedelta, time
from math import floor
import hashlib

id_student = 1#int(cursor.fetchall()[0][0])

def get_students():
    global id_student
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM student')
    students = [{'id': x[0], 'name': x[1], 'selected': x[0] == id_student} for x in cursor.fetchall()]
    cursor.close()
    return students

def get_group_id(_id_student):
    cursor = conn.cursor()
    print(_id_student)
    cursor.execute('SELECT group_id FROM student WHERE id = ' + str(_id_student))
    c = cursor.fetchall()[0][0]
    cursor.close()
    return c

@app.route('/home')
@app.route('/')
def home():
    print('heeeeeete')
    return render_template('home.html', students=get_students(), is_admin=is_admin)

@app.route('/', methods=['GET', 'POST'])
def update():
    if request.method == 'POST' and is_admin:
        global id_student
        id_student = int(request.form.get('select_stud'))
    return redirect(url_for('group'))

@app.route('/group')
def group():
    id_group = get_group_id(id_student)
    cursor = conn.cursor()

    cursor.execute('SELECT chair FROM "group" where id = ' + str(id_group) + ';')
    name_group = cursor.fetchall()[0][0]
    cursor.execute('SELECT name FROM student where group_id = ' + str(id_group) + ';')
    students = [x[0] for x in cursor.fetchall()]
    group = {
        'name': name_group,
        'students': students
    }
    cursor.close()
    return render_template('group.html', title='Список группы', group=group, students=get_students(), is_admin=is_admin)

@app.route('/schedule_week')
def schedule_week():
    cursor = conn.cursor()
    id_group = get_group_id(id_student)
    begin_week = datetime.today() - timedelta(days=datetime.today().isoweekday() - 1)
    cursor.execute(f"SELECT schedule.date_time, lecturer.name, subject.title, classroom.title from schedule \
        join lecturer on lecturer_id = lecturer.id \
        join subject on subject_id = subject.id \
        join classroom on classroom_id = classroom.id \
        where (date_time, INTERVAL '1 days') OVERLAPS (DATE '{begin_week.year}-{begin_week.month}-{begin_week.day}', INTERVAL '7 days') AND group_id = {id_group};")
            #  id |      date_time      | lecturer_id | subject_id | group_id | classroom_id 
    week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    schedule = [[[] for j in range(7)] for i in range(9)]
    for data in cursor.fetchall():
        schedule[floor((data[0].hour * 60 + data[0].minute - 8 * 60 - 30) / 1.5 / 60)][data[0].isoweekday() - 1].append(
            {'lecturer': data[1], 'subject': data[2], 'classroom': data[3]})
    cursor.close()
    # schedule =  {# пары, # препода, № предмета, № аудитории}
    return render_template('schedule_week.html', title='Расписание', week=week, schedule=schedule, count=len(schedule), students=get_students(), is_admin=is_admin)

@app.route('/homework')
def homework():
    cursor = conn.cursor()
    cursor.execute(f'select his_task.task_id, subject.title from \
        (select task.id as task_id, task.subject_id from\
        task join curriculum\
        on task.subject_id = curriculum.subject_id\
        join student\
        on curriculum.group_id = student.group_id\
        where student.id = {id_student}) as his_task left outer join \
        (select * from mark where student_id = {id_student}) as mark_for\
        on his_task.task_id = mark_for.task_id\
        join subject on his_task.subject_id = subject.id\
        where mark is null;')
    subjects = {}
    for x in cursor.fetchall():
        print(x)
        if not (x[1] in subjects):
            subjects[x[1]] = []
        subjects[x[1]].append("№ " + str(x[0]))
    return render_template('homework.html', title='Задания на дом', subjects=subjects, students=get_students(), is_admin=is_admin)

@app.route('/best')
def best():
    cursor = conn.cursor()
    id_group = get_group_id(id_student);
    print(id_group)
    cursor.execute('SELECT chair FROM "group" where id = ' + str(id_group) + ';')
    name_group = cursor.fetchall()[0][0]
    cursor.execute(f'select student.name, coalesce(CAST(count_mark as FLOAT) / CAST(count_task as FLOAT), 0) from\
        (select count(task.id) as count_task, student.id as student_id, student.name as name from \
        task join curriculum\
        on task.subject_id = curriculum.subject_id\
        join student\
        on curriculum.group_id = student.group_id\
        group by student.id) as his_task\
        join (select sum(mark.mark) as count_mark, student_id\
        from mark group by student_id) as his_marks\
        on his_task.student_id = his_marks.student_id\
        right outer join student on his_task.student_id = student.id\
        where group_id = {id_group};')
    top_list = cursor.fetchall()
    cursor.close()
    group = {
        'name': name_group,
        'students': [ {'name': x[0], 'progress': round(x[1], 2)} for x in top_list]}
    group['students'] = sorted(group['students'], key=lambda x: x['progress'], reverse=True)
    return render_template('best_students.html', group=group, students=get_students(), is_admin=is_admin)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global is_admin
    if request.method == 'POST':
        print("-------------------")
        login = request.form['login']
        password = int(hashlib.sha1(request.form["pass"].encode()).hexdigest(), 16) % 10000
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reg_info WHERE '" + login + "' = login and pass = " + str(password) + ";")
        if len(cursor.fetchall()) > 0:
            is_admin = True
            flash('Вход выполнен')
            return redirect(url_for('home'))
        else:
            flash('Неверный логин или пароль')
        cursor.close()
        return redirect(url_for('group'))
    return render_template('login.html', is_admin=is_admin)


@app.route('/add_group', methods=['GET', 'POST'])
def add_group():
    if request.method == 'POST' and is_admin:
        x = request.form["stop"]
        if x == 'true':
            flash('stop')
            print('stop')
            return render_template('add_group.html', is_admin=is_admin)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "group" (chair) VALUES (\''+ request.form['name'] +'\');')
        cursor.execute(f'select max(foo.id), foo.chair from\
             (select * from "group" where chair = \'{request.form["name"]}\') as foo\
             group by foo.chair;')
        # conn.rollback()
        conn.commit()
        try:
            x = cursor.fetchall()
            flash(f'Создана группа, id: {x[0][0]}, title: {x[0][1]}')    
        except:
            flash('Что-то пошло не так, обратитесь к разработчику')  
        cursor.close()
    return render_template('add_group.html', is_admin=is_admin)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    with conn.cursor() as cursor:
        cursor.execute('select * from "group";')
        groups = [{'id': x[0], 'chair': x[1]} for x in cursor.fetchall()]
    if request.method == 'POST' and is_admin:
        if request.form["stop"] == 'true':
            print('stop')
            return render_template('add_student.html', is_admin=is_admin)
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO student (group_id, name, birth, admission)\
                VALUES ({int(request.form.get("group_id"))},\'{request.form["name"]}\',\
                \'{request.form["bith"]}\', \'{request.form["admission"]}\');')
            cursor.execute('select id, group_id, name, birth, admission from\
                 (select max(id) as maxid from student) as foo\
                 join student on id = maxid;')
            try:
                x = cursor.fetchall()
                print(x)
                flash(f'Добавлен студент, id: {x[0][0]}, номер группы: {x[0][1]},\
                ФИО: {x[0][2]}, дата рождения: {x[0][3]}, \
                дата поступления: {x[0][0]}')
            except:
                flash('Что-то пошло не так, обратитесь к разработчику')     
        conn.commit()
    return render_template('add_student.html', groups=groups, is_admin=is_admin)

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST' and is_admin:
        if request.form["stop"] == 'true':
            return render_template('add_subject.html', is_admin=is_admin)
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO subject (title)\
                VALUES (\'{request.form["title"]}\');')
            cursor.execute('select id, title from (select max(id) as maxid from subject) as foo\
                join subject on id = maxid;')
            try:
                x = cursor.fetchall()
                flash(f'Добавлен предмет, id: {x[0][0]}, title: {x[0][1]}')
            except:
                flash('Что-то пошло не так, обратитесь к разработчику')     
        conn.commit()
    return render_template('add_subject.html', is_admin=is_admin)

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    with conn.cursor() as cursor:
        cursor.execute('select * from subject;')
        subjects = [{'id': x[0], 'title': x[1]} for x in cursor.fetchall()]
    if request.method == 'POST' and is_admin:
        if request.form["stop"] == 'true':
            return render_template('add_task.html', is_admin=is_admin)
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO task (subject_id)\
                VALUES ({int(request.form.get("subject_id"))});')
            cursor.execute('select id, subject_id from (select max(id) as maxid from task) as foo\
                 join task on id = maxid;')
            try:
                x = cursor.fetchall()
                flash(f'Добавлено задание, id: {x[0][0]}, номер предмета: {x[0][1]}')
            except:
                flash('Что-то пошло не так, обратитесь к разработчику')  
        conn.commit()
    return render_template('add_task.html', subjects=subjects, is_admin=is_admin)

@app.route('/add_curr', methods=['GET', 'POST'])
def add_curr():
    with conn.cursor() as cursor:
        cursor.execute('select * from subject;')
        subjects = [{'id': x[0], 'title': x[1]} for x in cursor.fetchall()]
    with conn.cursor() as cursor:
        cursor.execute('select * from "group";')
        groups = [{'id': x[0], 'title': x[1]} for x in cursor.fetchall()]
    if request.method == 'POST' and is_admin:
        try:
            if request.form["stop"] == 'true':
                return render_template('add_curr.html', is_admin=is_admin)
            with conn.cursor() as cursor:
                cursor.execute(f'INSERT INTO curriculum (subject_id, group_id)\
                    VALUES ({int(request.form.get("subject_id"))}, {int(request.form.get("group_id"))});')
                cursor.execute(f'select subject_id, group_id from curriculum \
                    where subject_id={int(request.form.get("subject_id"))}, group_id = {int(request.form.get("group_id"))};')
                x = cursor.fetchall()
                flash(f'Добавлена связь, номер предмета: {x[0][1]}, номер группы: {x[0][2]}')
            conn.commit()
        except:
            flash('Что-то пошло не так, обратитесь к разработчику')  
    return render_template('add_curr.html', subjects=subjects, groups=groups, is_admin=is_admin)


@app.route('/add_schedule', methods=['GET', 'POST'])
def add_schedule():
    with conn.cursor() as cursor:
        cursor.execute('select * from lecturer;')
        lecturers = [{'id': x[0], 'name': x[1]} for x in cursor.fetchall()]
        cursor.execute('select * from subject;')
        subjects = [{'id': x[0], 'title': x[1]} for x in cursor.fetchall()]
        cursor.execute('select * from "group";')
        groups = [{'id': x[0], 'chair': x[1]} for x in cursor.fetchall()]
        cursor.execute('select * from classroom;')
        classrooms = [{'id': x[0], 'title': x[1]} for x in cursor.fetchall()]
    if request.method == 'POST' and is_admin:
        if request.form["stop"] == 'true':
            return render_template('add_schedule.html', is_admin=is_admin)
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO schedule (date_time, lecturer_id, subject_id, group_id, classroom_id)\
                VALUES (\'{request.form["date_time"]}\', {int(request.form["lecturer_id"])},\
                {int(request.form["subject_id"])}, {int(request.form["group_id"])}, {int(request.form["classroom_id"])});')
            cursor.execute('select id, date_time, lecturer_id, subject_id, group_id, classroom_id\
                 from (select max(id) as maxid from schedule) as foo\
                 join schedule on id = maxid;')
            conn.commit()
            try:
                x = cursor.fetchall()
                flash(f'Добавлена пара, id: {x[0][0]}, дата и время начала: {x[0][1]},\
                номер преподавателя: {x[0][2]}, номер предмета: {x[0][3]},\
                номер группы: {x[0][4]}, номер аудитории: {x[0][5]}')
            except:
                flash('Что-то пошло не так, обратитесь к разработчику')  
        conn.commit()
    return render_template('add_schedule.html', lecturers=lecturers, subjects=subjects,
        groups=groups, classrooms=classrooms, is_admin=is_admin)

@app.route('/add_mark', methods=['GET', 'POST'])
def add_mark():
    with conn.cursor() as cursor:
        cursor.execute('select id, name from student;')
        students = [{'id': x[0], 'name': x[1]} for x in cursor.fetchall()]
        cursor.execute('select * from task;')
        tasks = [{'id': x[0]} for x in cursor.fetchall()]
    if request.method == 'POST' and is_admin:
        if request.form["stop"] == 'true':
            return render_template('add_mark.html', is_admin=is_admin)
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO mark (student_id, task_id, mark)\
                VALUES (\'{int(request.form["student_id"])}\', {int(request.form["task_id"])},\
                {request.form["mark"]});')
            cursor.execute('select mark.id, mark, name\
                 from (select max(id) as maxid from mark) as foo\
                    join mark on maxid=mark.id join student on mark.student_id = student.id;')
            try:
                x  = cursor.fetchall()
                flash(f'Добавлена оценка: id: {x[0][0]}, оценка: {x[0][1]},\
                имя: {x[0][2]}')
            except:
                flash('Что-то пошло не так, обратитесь к разработчику')  
        conn.commit()
    return render_template('add_mark.html', students=students, tasks=tasks, is_admin=is_admin)