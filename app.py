import os
import random
import sqlite3

from flask import Flask, g, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt

TRANSLATIONS = {
    'en': {
        'dashboard': 'Dashboard',
        'my_dashboard': 'My Dashboard',
        'teacher_dashboard': 'Teacher Dashboard',
        'admin_dashboard': 'Admin Dashboard',
        'welcome': 'Welcome',
        'sign_in': 'Sign in',
        'sign_out': 'Sign out',
        'register': 'Register',
        'profile': 'Profile',
        'profile_settings': 'Profile Settings',
        'save_changes': 'Save Changes',
        'cancel': 'Cancel',
        'full_name': 'Full Name',
        'email': 'Email',
        'username': 'Username',
        'password': 'Password',
        'current_password': 'Current Password',
        'new_password': 'New Password',
        'confirm_password': 'Confirm Password',
        'change_password': 'Change Password',
        'courses': 'Courses',
        'audit_log': 'Audit Log',
        'menu': 'Menu',
        'overview': 'Overview',
        'morning': 'Good Morning',
        'afternoon': 'Good Afternoon',
        'hi': 'Hi',
        'settings_updated': 'Settings updated successfully.',
        'password_changed': 'Password changed successfully.',
        'invalid_password': 'Current password is incorrect.',
        'invalid_credentials': 'Invalid username or password.',
        'language': 'Language',
        'en': 'EN',
        'zh': '中文',
        'admin_role': 'Admin',
        'teacher_role': 'Teacher',
        'student_role': 'Student',
        'admin_desc': 'Oversee system & users',
        'teacher_desc': 'Manage grades & reports',
        'student_desc': 'View scores & progress',
        'role_hint': 'Tap an account type above, then enter your credentials.',
        'role_hint_selected': 'Now enter your',
        'credentials': 'credentials.',
        'no_account': "Don't have an account?",
        'register_with_code': 'Register with enrollment code',
        'student_registration': 'Student Registration',
        'enrollment_code': 'Enrollment Code',
        'enrollment_placeholder': 'Provided by your teacher',
        'set_password': 'Set password',
        'password_requirements': '8+ chars, uppercase, lowercase, digit & special char (e.g. Caplow@123)',
        'already_have_account': 'Already have an account?',
        'login': 'Login',
        'passwords_match': 'Passwords match',
        'passwords_no_match': 'Passwords do not match',
        'password_strength': 'Password strength:',
        'weak': 'Weak',
        'medium': 'Medium',
        'strong': 'Strong',
        'view_grades': 'View Grades',
        'student_portal': 'student portal',
        'welcome_student_desc': 'Check your grades, track your progress, and stay on top of your courses.',
        'welcome_subtitle_student': 'Welcome,',
        'enrolled_courses': 'Here are your enrolled courses.',
        'no_courses': 'You are not enrolled in any courses yet.',
        'course': 'Course',
        'close': 'Close',
        'assignments': 'Assignments',
        'analytics': 'Analytics',
        'resources': 'Resources',
        'recent_assignments': 'Recent assignments and scores for this course.',
        'quiz_results': 'Quiz Results',
        'performance_distribution': 'Performance distribution across categories.',
        'course_resources': 'Course resources and materials.',
        'no_resources': 'No resources available yet.',
        'welcome_teacher': 'Welcome to your teacher portal. Manage your courses, grades, and class performance.',
        'teacher_portal': 'teacher portal',
        'teacher_subtitle': 'Welcome,',
        'system_overview': 'System overview and quick actions',
        'welcome_admin': 'Here\'s your system overview. Monitor courses, users, and recent activity.',
        'admin_portal': 'system overview',
        'admin_subtitle': 'Monitor courses, users, and recent activity all in one place.',
        'active_courses': 'Active Courses',
        'total_teachers': 'Total Teachers',
        'total_students': 'Total Students',
        'enrollments': 'Enrollments',
        'recent_activity': 'Recent Audit Activity',
        'view_all': 'View All',
        'quick_actions': 'Quick Actions',
        'create_course': 'Create Course',
        'manage_users': 'Manage Users',
        'export_reports': 'Export Reports',
        'my_courses': 'My Courses',
        'teacher_welcome_subtitle': 'Manage your courses, track grades, and monitor class performance.',
        'create': 'Create',
        'edit': 'Edit',
        'delete': 'Delete',
        'are_you_sure': 'Are you sure?',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'students': 'Students',
        'failing': 'Failing',
        'class_average': 'Class Average',
        'enrolled': 'enrolled',
        'avg': 'avg',
        'no_scores': 'No scores',
        'no_courses_assigned': 'You have no courses assigned yet.',
        'no_grade_changes': 'No grade changes yet.',
        'grades': 'Grades',
        'categories': 'Categories',
        'report': 'Report',
        'export': 'Export',
        'teaching_dashboard': 'teaching dashboard',
        'teacher_welcome_desc': 'Manage courses, enter grades, and track student performance.',
        'item_label': 'Item',
        'your_score': 'Your Score',
        'max_score': 'Max Score',
        'weight_label': 'Weight',
        'na': 'N/A',
        'pending': 'Pending',
        'contribution': 'Contribution:',
        'overall': 'Overall',
        'back_to_dashboard': 'Back to Dashboard',
        'grade_entry': 'Grade Entry',
        'no_students_enrolled': 'No students enrolled in this course.',
        'save_all_scores': 'Save All Scores',
        'back': 'Back',
        'grade_categories_items': 'Grade Categories &amp; Items',
        'grades_locked_msg': 'Grades have already been entered for this course. Categories and items are locked and cannot be changed.',
        'add_category': 'Add Category',
        'category_name': 'Category Name',
        'weight_percent': 'Weight %',
        'add': 'Add',
        'remaining': 'Remaining: ',
        'category': 'Category',
        'weight': 'Weight',
        'item_plural': 'Items',
        'no_items': 'No items',
        'item_name': 'Item name',
        'add_item': 'Add Item',
        'locked': 'Locked',
        'total': 'Total',
        'weights_should_total': 'Weights should total exactly 100%. Current total: ',
        'add_or_edit_categories': 'Add or edit categories to reach 100%.',
        'edit_category': 'Edit Category',
        'weight_percentage': 'Weight (%)',
        'save': 'Save',
        'grade_report': 'Grade Report',
        'highest_score': 'Highest Score',
        'lowest_score': 'Lowest Score',
        'grade_summary': 'Grade Summary',
        'export_csv': 'Export CSV',
        'export_grades': 'Export Grades',
        'export_summary': 'Export Summary',
        'csv_description': 'The CSV file will include student names, scores for all grade items, computed averages, and letter grades, as well as overall statistics.',
        'confirm_export': 'Download CSV',
        'csv_preview': 'CSV Preview',
        'rows': 'rows',
        'scroll_to_see_all': 'Scroll to see all columns',
        'recently_used': 'Recently Used',
        'frequently_used': 'Frequently Used',
        'no_recent_courses': 'No recently accessed courses.',
        'no_freq_courses': 'No frequently accessed courses yet.',
        'grade_distribution': 'Grade Distribution',
        'missing_zero_items': 'Missing/Zero Items',
        'no_failing_students': 'No failing students.',
        'manage_courses': 'Manage Courses',
        'create_and_manage': 'Create and manage course offerings.',
        'course_list': 'Course List',
        'code_label': 'Code',
        'name_label': 'Name',
        'credits_label': 'Credits',
        'teacher_label': 'Teacher',
        'enroll_code': 'Enroll Code',
        'assign': 'Assign',
        'unassigned': 'Unassigned',
        'set_teacher': 'Set',
        'no_courses_yet': 'No courses yet. Create one above.',
        'code_placeholder': 'Code e.g. CS101',
        'course_name_placeholder': 'Course Name',
        'auto_generated': 'Enrollment code auto-generated',
        'track_grade_changes': 'Track all grade changes across courses.',
        'all_courses_filter': 'All Courses',
        'all_teachers_filter': 'All Teachers',
        'filter': 'Filter',
        'clear': 'Clear',
        'date_label': 'Date',
        'changed_by': 'Changed By',
        'old_score': 'Old Score',
        'new_score': 'New Score',
        'no_entries_yet': 'No entries yet.',
        'change_log': 'Change Log',
        'entries': 'entries',
        'manage_enrollments': 'Manage enrollments for this course.',
        'no_enrolled': 'No students enrolled.',
        'edit_course': 'Edit Course',
        'edit_courses': 'Edit Courses',
        'select_course_to_edit': 'Select a course below to edit its details.',
        'course_code': 'Course Code',
        'course_name': 'Course Name',
        'enrollment_code': 'Enrollment Code',
        'auto_generated_on_create': 'Auto-generated on creation.',
        'enrolled_students': 'Enrollments',
        'enrolled_at': 'Enrolled At',
        'avg_grade': 'Avg Grade',
        'unenroll_selected': 'Unenroll Selected',
        'available_students': 'Available Students',
        'enroll_selected': 'Enroll Selected',
        'all_students_enrolled': 'All students enrolled.',
        'back_to_courses': 'Back to Courses',
        'grade': 'Grade',
        'class_avg_short': 'Class Avg',
        'class_average_label': 'Class Average:',
        'failing_students': 'Failing Students',
        'students_label': 'Students',
        'student': 'Student',
        'average': 'Average',
        'name': 'Name',
        'actions': 'Actions',
        'items': 'Items',
        'category_label': 'Category',
        'enter_grades': 'Enter Grades',
        'grade_letter': 'Grade',
        'save_changes': 'Save Changes',
        'max_prefix': 'max ',
        'import': 'Import',
        'all_courses_summary': 'All Courses Summary',
        'add_course': '+ Add Course',
        'view': 'View',
        'today': 'Today',
        'changed': 'changed',
        'at_risk': 'At risk',
        'score_below_60': 'score below 60',
        'overall_avg': 'Overall avg',
        'best_grade': 'Best grade',
        'your_grades_by_course': 'Your grades by course',
        'score_trend': 'Score trend',
        'change_course': 'change course',
        'this_semester': 'this semester',
        'across_all_courses': 'across all courses',
        'enrolled_lower': 'enrolled',
        'lessons': 'Lessons',
        'schedule': 'Schedule',
        'materials': 'Materials',
        'forum': 'Forum',
        'settings': 'Settings',
        'help': 'Help',
        'users': 'Users',
        'reports': 'Reports',
    },
    'zh': {
        'dashboard': '仪表盘',
        'my_dashboard': '我的仪表盘',
        'teacher_dashboard': '教师仪表盘',
        'admin_dashboard': '管理仪表盘',
        'welcome': '欢迎',
        'sign_in': '登录',
        'sign_out': '退出登录',
        'register': '注册',
        'profile': '个人资料',
        'profile_settings': '个人设置',
        'save_changes': '保存修改',
        'cancel': '取消',
        'full_name': '姓名',
        'email': '邮箱',
        'username': '用户名',
        'password': '密码',
        'current_password': '当前密码',
        'new_password': '新密码',
        'confirm_password': '确认密码',
        'change_password': '修改密码',
        'courses': '课程管理',
        'audit_log': '审计日志',
        'menu': '菜单',
        'overview': '概览',
        'morning': '早上好',
        'afternoon': '下午好',
        'hi': '你好',
        'settings_updated': '设置已更新。',
        'password_changed': '密码已修改。',
        'invalid_password': '当前密码不正确。',
        'invalid_credentials': '用户名或密码错误。',
        'language': '语言',
        'en': 'EN',
        'zh': '中文',
        'admin_role': '管理员',
        'teacher_role': '教师',
        'student_role': '学生',
        'admin_desc': '管理系统与用户',
        'teacher_desc': '管理成绩与报告',
        'student_desc': '查看成绩与进度',
        'role_hint': '点击上方账户类型，然后输入您的凭据。',
        'role_hint_selected': '现在输入',
        'credentials': '凭据。',
        'no_account': '没有账户？',
        'register_with_code': '使用注册码注册',
        'student_registration': '学生注册',
        'enrollment_code': '注册码',
        'enrollment_placeholder': '由您的老师提供',
        'set_password': '设置密码',
        'password_requirements': '至少8个字符，包含大写、小写、数字和特殊字符（例如 Caplow@123）',
        'already_have_account': '已有账户？',
        'login': '登录',
        'passwords_match': '密码匹配',
        'passwords_no_match': '密码不匹配',
        'password_strength': '密码强度：',
        'weak': '弱',
        'medium': '中',
        'strong': '强',
        'view_grades': '查看成绩',
        'student_portal': '学生门户',
        'welcome_student_desc': '查看成绩，跟踪进度，掌握课程动态。',
        'welcome_subtitle_student': '欢迎，',
        'enrolled_courses': '以下是您已注册的课程。',
        'no_courses': '您还没有注册任何课程。',
        'course': '课程',
        'close': '关闭',
        'assignments': '作业',
        'analytics': '分析',
        'resources': '资源',
        'recent_assignments': '该课程最近的作业和成绩。',
        'quiz_results': '测验结果',
        'performance_distribution': '各分类的成绩分布。',
        'course_resources': '课程资源和材料。',
        'no_resources': '暂无可用资源。',
        'welcome_teacher': '欢迎使用教师门户。管理您的课程、成绩和班级表现。',
        'teacher_portal': '教师门户',
        'teacher_subtitle': '欢迎，',
        'system_overview': '系统概览与快捷操作',
        'welcome_admin': '这是您的系统概览。管理课程、用户和最近活动。',
        'admin_portal': '系统概览',
        'admin_subtitle': '在一个地方管理课程、用户和最近活动。',
        'active_courses': '活跃课程',
        'total_teachers': '教师总数',
        'total_students': '学生总数',
        'enrollments': '注册人数',
        'recent_activity': '最近审计活动',
        'view_all': '查看全部',
        'quick_actions': '快捷操作',
        'create_course': '创建课程',
        'manage_users': '管理用户',
        'export_reports': '导出报告',
        'my_courses': '我的课程',
        'teacher_welcome_subtitle': '管理您的课程，跟踪成绩，监控班级表现。',
        'create': '创建',
        'edit': '编辑',
        'delete': '删除',
        'are_you_sure': '确定吗？',
        'confirm': '确认',
        'cancel': '取消',
        'students': '学生',
        'failing': '不及格',
        'class_average': '班级平均分',
        'enrolled': '已注册',
        'avg': '平均分',
        'no_scores': '暂无成绩',
        'no_courses_assigned': '您还没有分配任何课程。',
        'no_grade_changes': '暂无成绩更改。',
        'grades': '成绩',
        'categories': '分类',
        'report': '报告',
        'export': '导出',
        'teaching_dashboard': '教学仪表盘',
        'teacher_welcome_desc': '管理课程，录入成绩，跟踪学生表现。',
        'item_label': '项目',
        'your_score': '你的成绩',
        'max_score': '最高分',
        'weight_label': '权重',
        'na': '暂无',
        'pending': '待定',
        'contribution': '贡献：',
        'overall': '总分',
        'back_to_dashboard': '返回仪表盘',
        'grade_entry': '成绩录入',
        'no_students_enrolled': '该课程没有学生注册。',
        'save_all_scores': '保存所有成绩',
        'back': '返回',
        'grade_categories_items': '成绩分类与项目',
        'grades_locked_msg': '该课程已有成绩记录。分类和项目已被锁定，无法更改。',
        'add_category': '添加分类',
        'category_name': '分类名称',
        'weight_percent': '权重 %',
        'add': '添加',
        'remaining': '剩余：',
        'category': '分类',
        'weight': '权重',
        'item_plural': '项目',
        'no_items': '暂无项目',
        'item_name': '项目名称',
        'add_item': '添加项目',
        'locked': '已锁定',
        'total': '总计',
        'weights_should_total': '权重总和必须为 100%。当前总计：',
        'add_or_edit_categories': '添加或编辑分类以达到 100%。',
        'edit_category': '编辑分类',
        'weight_percentage': '权重（%）',
        'save': '保存',
        'grade_report': '成绩报告',
        'highest_score': '最高分',
        'lowest_score': '最低分',
        'grade_summary': '成绩总结',
        'export_csv': '导出 CSV',
        'export_grades': '导出成绩',
        'export_summary': '导出摘要',
        'csv_description': 'CSV 文件将包含学生姓名、所有评分项目的分数、计算出的平均分和等级，以及总体统计信息。',
        'confirm_export': '下载 CSV',
        'csv_preview': 'CSV 预览',
        'rows': '行',
        'scroll_to_see_all': '滚动查看所有列',
        'recently_used': '最近使用',
        'frequently_used': '频繁使用',
        'no_recent_courses': '暂无最近访问的课程。',
        'no_freq_courses': '暂无频繁访问的课程。',
        'grade_distribution': '成绩分布',
        'missing_zero_items': '缺失/零分项目',
        'no_failing_students': '没有不及格学生。',
        'manage_courses': '管理课程',
        'create_and_manage': '创建和管理课程。',
        'course_list': '课程列表',
        'code_label': '代码',
        'name_label': '名称',
        'credits_label': '学分',
        'teacher_label': '教师',
        'enroll_code': '注册码',
        'assign': '分配',
        'unassigned': '未分配',
        'set_teacher': '设置',
        'no_courses_yet': '暂无课程。请在上面创建。',
        'code_placeholder': '代码，如 CS101',
        'course_name_placeholder': '课程名称',
        'auto_generated': '注册码自动生成',
        'track_grade_changes': '跟踪所有课程的成绩变更。',
        'all_courses_filter': '所有课程',
        'all_teachers_filter': '所有教师',
        'filter': '筛选',
        'clear': '清除',
        'date_label': '日期',
        'changed_by': '更改人',
        'old_score': '原成绩',
        'new_score': '新成绩',
        'no_entries_yet': '暂无记录。',
        'change_log': '更改日志',
        'entries': '条记录',
        'manage_enrollments': '管理此课程的注册信息。',
        'no_enrolled': '暂无注册学生。',
        'edit_course': '编辑课程',
        'edit_courses': '编辑课程',
        'select_course_to_edit': '选择下方课程以编辑其详细信息。',
        'course_code': '课程代码',
        'course_name': '课程名称',
        'enrollment_code': '注册码',
        'auto_generated_on_create': '创建时自动生成。',
        'enrolled_students': '注册管理',
        'enrolled_at': '注册时间',
        'avg_grade': '平均分',
        'unenroll_selected': '取消注册',
        'available_students': '可选学生',
        'enroll_selected': '注册选定',
        'all_students_enrolled': '所有学生已注册。',
        'back_to_courses': '返回课程列表',
        'grade': '等级',
        'class_avg_short': '班级平均',
        'class_average_label': '班级平均分：',
        'failing_students': '不及格学生',
        'students_label': '学生人数',
        'student': '学生',
        'average': '平均分',
        'name': '姓名',
        'actions': '操作',
        'items': '项目',
        'category_label': '分类',
        'enter_grades': '录入成绩',
        'grade_letter': '等级',
        'max_prefix': '满分 ',
        'all_courses_summary': '所有课程摘要',
        'add_course': '+ 添加课程',
        'view': '查看',
        'today': '今日',
        'changed': '修改了',
        'at_risk': '不及格风险',
        'score_below_60': '分数低于60',
        'overall_avg': '总平均分',
        'best_grade': '最高等级',
        'your_grades_by_course': '各课程成绩',
        'score_trend': '成绩趋势',
        'change_course': '切换课程',
        'this_semester': '本学期',
        'across_all_courses': '所有课程',
        'enrolled_lower': '已注册',
        'lessons': '课程',
        'schedule': '日程',
        'materials': '资料',
        'forum': '论坛',
        'settings': '设置',
        'help': '帮助',
        'users': '用户',
        'reports': '报告',
    },
}

bcrypt = Bcrypt()


def get_db():
    if 'db' in g:
        return g.db
    db_path = os.environ.get('TEST_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grades.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    g.db = conn
    return g.db

def init_db():
    db_path = os.environ.get('TEST_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grades.db')
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    schema = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def seed_db():
    db_path = os.environ.get('TEST_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grades.db')
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        db.close()
        return
    pw = lambda p: bcrypt.generate_password_hash(p).decode('utf-8')

    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('admin', pw('admin123'), 'Admin User', 'admin@gradems.com', 'admin'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('teacher1', pw('teacher123'), 'Dr. Ahmed', 'ahmed@gradems.com', 'teacher'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('teacher2', pw('teacher123'), 'Dr. Sara', 'sara@gradems.com', 'teacher'))
    for i in range(1, 11):
        uid = f'L202610{i:02d}'
        db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
                   (uid, pw('student123'), f'Student {i}', f'{uid}@student.com', 'student'))

    t1 = db.execute("SELECT id FROM users WHERE username='teacher1'").fetchone()['id']
    t2 = db.execute("SELECT id FROM users WHERE username='teacher2'").fetchone()['id']
    student_ids = [r['id'] for r in db.execute("SELECT id FROM users WHERE role='student' ORDER BY id").fetchall()]

    db.execute("INSERT INTO courses (course_code,course_name,credits,teacher_id,enrollment_code) VALUES (?,?,?,?,?)",
               ('CS101', 'Intro to Programming', 3, t1, 'A1B2C3D4'))
    db.execute("INSERT INTO courses (course_code,course_name,credits,teacher_id,enrollment_code) VALUES (?,?,?,?,?)",
               ('CS201', 'Data Structures', 3, t2, 'E5F6G7H8'))
    db.execute("INSERT INTO courses (course_code,course_name,credits,teacher_id,enrollment_code) VALUES (?,?,?,?,?)",
               ('MA101', 'Calculus I', 4, t1, 'I9J0K1L2'))

    course_ids = [r['id'] for r in db.execute("SELECT id FROM courses ORDER BY id").fetchall()]
    for s_id in student_ids:
        for c_id in course_ids:
            db.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)", (s_id, c_id))

    cats_data = [
        (course_ids[0], 'Assignments', 30), (course_ids[0], 'Midterm', 30), (course_ids[0], 'Final', 40),
        (course_ids[1], 'Assignments', 40), (course_ids[1], 'Exams', 60),
        (course_ids[2], 'Homework', 20), (course_ids[2], 'Midterm', 30), (course_ids[2], 'Final', 50),
    ]
    for c_id, cat_name, weight in cats_data:
        db.execute("INSERT INTO grade_categories (course_id,category_name,weight) VALUES (?,?,?)",
                   (c_id, cat_name, weight))

    for c_id in course_ids:
        cats = db.execute("SELECT id,category_name FROM grade_categories WHERE course_id=?", (c_id,)).fetchall()
        for cat in cats:
            for j in range(1, 3):
                db.execute("INSERT INTO grade_items (category_id,item_name,max_score) VALUES (?,?,?)",
                           (cat['id'], f'{cat["category_name"]} {j}', 100))

    for s_id in student_ids:
        items = db.execute(
            "SELECT gi.id FROM grade_items gi JOIN grade_categories gc ON gi.category_id=gc.id WHERE gc.course_id=?",
            (course_ids[0],)).fetchall()
        for item in items:
            score = round(50 + random.random() * 50, 1)
            db.execute("INSERT INTO scores (student_id,grade_item_id,score) VALUES (?,?,?)",
                       (s_id, item['id'], score))
    db.commit()
    db.close()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'gradems-dev-key')
    if app.secret_key == 'gradems-dev-key':
        import sys as _sys
        _sys.stderr.write('Warning: Using default SECRET_KEY for development. '
                          'Set SECRET_KEY environment variable for production.\n')

    if not os.path.exists(
        os.environ.get('TEST_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grades.db')
    ):
        init_db()
        seed_db()

    bcrypt.init_app(app)

    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.teacher import teacher_bp
    from blueprints.student import student_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.errorhandler(404)
    def handle_404(e):
        return render_template('404.html'), 404

    @app.context_processor
    def inject_csrf():
        from utils.helpers import generate_csrf_token
        current_lang = session.get('lang', 'en')
        t = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
        def _(key):
            return t.get(key, key)
        return dict(csrf_token=generate_csrf_token(), now=__import__('datetime').datetime.now, _=_, current_lang=current_lang)

    @app.teardown_appcontext
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)