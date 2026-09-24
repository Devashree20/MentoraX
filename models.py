from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('hod', 'HOD'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # Use roll_no as the unique identifier for students. Mentors can use staff id or email.
    roll_no = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    mentor = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='mentored_students',
        limit_choices_to={'role': 'mentor'}
    )
    
    # Step 1: Registration Details
    name = models.CharField(max_length=255)
    roll_no = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    batch = models.CharField(max_length=50)
    
    # Step 2: Personal Details
    dob = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=20, null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, null=True, blank=True)
    degree = models.CharField(max_length=50, null=True, blank=True) # UG/PG
    section = models.CharField(max_length=10, null=True, blank=True)
    cut_off_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    admission_number = models.CharField(max_length=50, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=(('MQ', 'MQ'), ('GQ', 'GQ')), null=True, blank=True)
    
    # PG only details
    ug_degree_info = models.TextField(help_text="UG DEGREE WITH BRANCH AND COLLEGE", null=True, blank=True)
    
    tc_no = models.CharField(max_length=50, null=True, blank=True)
    tc_date = models.DateField(null=True, blank=True)
    mother_tongue = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    community = models.CharField(max_length=50, null=True, blank=True)
    identification_marks = models.TextField(null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    placement_willingness = models.BooleanField(default=True)
    communication_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Graduated', 'Graduated'),
        ('Dropped', 'Dropped'),
        ('Transferred', 'Transferred'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.name} ({self.roll_no})"

class ParentGuardianDetails(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='parent_details')
    
    # Father Details
    father_name = models.CharField(max_length=255, null=True, blank=True)
    father_occupation = models.CharField(max_length=255, null=True, blank=True)
    father_annual_income = models.CharField(max_length=100, null=True, blank=True)
    father_contact_no = models.CharField(max_length=20, null=True, blank=True)
    
    # Mother Details
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    mother_occupation = models.CharField(max_length=255, null=True, blank=True)
    mother_annual_income = models.CharField(max_length=100, null=True, blank=True)
    mother_contact_no = models.CharField(max_length=20, null=True, blank=True)
    
    # Guardian Details
    guardian_name = models.CharField(max_length=255, null=True, blank=True)
    guardian_occupation = models.CharField(max_length=255, null=True, blank=True)
    guardian_contact_no = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Parents of {self.student.name}"

class AcademicSemester(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField() # 1, 2, 3, 4, etc.
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    ccet1_overall = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ccet2_overall = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'semester_number')

class AcademicCourse(models.Model):
    semester = models.ForeignKey(AcademicSemester, on_delete=models.CASCADE, related_name='courses')
    course_name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50)
    ccet1_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ccet2_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ccet3_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    retest_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ese_grade = models.CharField(max_length=10, null=True, blank=True)
    month_year_of_passing = models.CharField(max_length=50, null=True, blank=True)



class ResidentialStatus(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='residential_status')
    year_1 = models.CharField(max_length=20, choices=(('H', 'Hosteller'), ('D', 'Day Scholar')), null=True, blank=True)
    year_2 = models.CharField(max_length=20, choices=(('H', 'Hosteller'), ('D', 'Day Scholar')), null=True, blank=True)
    year_3 = models.CharField(max_length=20, choices=(('H', 'Hosteller'), ('D', 'Day Scholar')), null=True, blank=True)
    year_4 = models.CharField(max_length=20, choices=(('H', 'Hosteller'), ('D', 'Day Scholar')), null=True, blank=True)

class Internship(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internships')
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    duration = models.CharField(max_length=100) # e.g. "3 months", "Summer 2024"
    stipend = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    certificate_link = models.URLField(null=True, blank=True)
    date_completed = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.role} at {self.company_name}"

class DisciplinaryAction(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='disciplinary_actions')
    date = models.DateField()
    description = models.TextField()
    remarks = models.TextField(null=True, blank=True)

class ParentInteraction(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='parent_interactions')
    date = models.DateField()
    purpose = models.TextField()
    remarks = models.TextField(null=True, blank=True)

class CoCurricularActivity(models.Model):
    ACTIVITY_CATEGORIES = (
        ('event', 'Event Participation'),
        ('hackathon', 'Hackathon'),
        ('workshop', 'Workshop'),
        ('other', 'Other'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='cocurricular_activities')
    category = models.CharField(max_length=20, choices=ACTIVITY_CATEGORIES, default='other')
    description = models.TextField()
    date_from = models.DateField()
    date_to = models.DateField(null=True, blank=True)
    place = models.CharField(max_length=255)
    remarks = models.TextField(null=True, blank=True)

class CounsellingRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='counselling_records')
    date = models.DateField()
    details = models.TextField()
    remarks = models.TextField(null=True, blank=True)

class LeaveLog(models.Model):
    LEAVE_TYPES = (
        ('leave', 'General Leave'),
        ('od', 'On Duty (OD)'),
        ('ml', 'Medical Leave (ML)'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='leaves')
    date_applied = models.DateField(auto_now_add=True)
    sem = models.IntegerField()
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES, default='leave')
    reason = models.TextField()
    date_from = models.DateField()
    date_to = models.DateField(null=True, blank=True)
    no_of_days = models.DecimalField(max_digits=4, decimal_places=1)

class ProjectDetails(models.Model):
    PROJECT_TYPES = (
        ('mini', 'Mini Project'),
        ('major', 'Major Project'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    project_type = models.CharField(max_length=10, choices=PROJECT_TYPES)
    title_domain = models.CharField(max_length=255)
    languages_used = models.CharField(max_length=255)
    description = models.TextField()
