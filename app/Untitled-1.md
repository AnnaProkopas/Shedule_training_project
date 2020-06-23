select *  from task
join mark
on task.id = mark.task_id
where mark.mark is null;

select *  from
task join curriculum
on task.subject_id = curriculum.subject_id
left outer join mark
on task.id = mark.task_id
join student
on curriculum.group_id = student.group_id
join subject
on task.subject_id = subject.id
where student.id = 6;

select his_task.task_id, subject.title from 
(select task.id as task_id, task.subject_id from
task join curriculum
on task.subject_id = curriculum.subject_id
join student
on curriculum.group_id = student.group_id
where student.id = 6) as his_task left outer join 
(select * from mark where student_id = 6) as mark_for
on his_task.task_id = mark_for.task_id
join subject on his_task.subject_id = subject.id
where mark is null;

select student.name, coalesce(CAST(count_mark as FLOAT) / CAST(count_task as FLOAT), 0) from
(select count(task.id) as count_task, student.id as student_id, student.name as name from
task join curriculum
on task.subject_id = curriculum.subject_id
join student
on curriculum.group_id = student.group_id
group by student.id) as his_task
join (select sum(mark.mark) as count_mark, student_id
from mark group by student_id) as his_marks
on his_task.student_id = his_marks.student_id
right outer join student on his_task.student_id = student.id;