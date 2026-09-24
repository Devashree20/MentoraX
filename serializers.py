from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    CustomUser, StudentProfile, ParentGuardianDetails, AcademicSemester,
    AcademicCourse, ResidentialStatus, DisciplinaryAction, ParentInteraction,
    CoCurricularActivity, CounsellingRecord, LeaveLog, ProjectDetails, Internship
)

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'roll_no', 'password', 'is_active']

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        roll_no = validated_data.get('roll_no')
        if not roll_no: # Handle empty string as None
            roll_no = None
            
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'student'),
            roll_no=roll_no,
            password=validated_data['password']
        )
        return user

class ParentGuardianDetailsSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentProfile.objects.all(), source='student', write_only=True
    )
    class Meta:
        model = ParentGuardianDetails
        fields = '__all__'

class AcademicCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicCourse
        fields = '__all__'
        extra_kwargs = {'semester': {'required': False}}

class AcademicSemesterSerializer(serializers.ModelSerializer):
    courses = AcademicCourseSerializer(many=True, required=False)
    
    class Meta:
        model = AcademicSemester
        fields = '__all__'

    def create(self, validated_data):
        courses_data = validated_data.pop('courses', [])
        semester = AcademicSemester.objects.create(**validated_data)
        for course_data in courses_data:
            AcademicCourse.objects.create(semester=semester, **course_data)
        return semester

    def update(self, instance, validated_data):
        courses_data = validated_data.pop('courses', [])
        # Update semester fields
        instance.semester_number = validated_data.get('semester_number', instance.semester_number)
        instance.attendance_percentage = validated_data.get('attendance_percentage', instance.attendance_percentage)
        instance.sgpa = validated_data.get('sgpa', instance.sgpa)
        instance.cgpa = validated_data.get('cgpa', instance.cgpa)
        instance.ccet1_overall = validated_data.get('ccet1_overall', instance.ccet1_overall)
        instance.ccet2_overall = validated_data.get('ccet2_overall', instance.ccet2_overall)
        instance.save()
        
        # Update/Recreate courses
        instance.courses.all().delete()
        for course_data in courses_data:
            AcademicCourse.objects.create(semester=instance, **course_data)
        return instance

class ResidentialStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidentialStatus
        fields = '__all__'

class DisciplinaryActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplinaryAction
        fields = '__all__'

class ParentInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentInteraction
        fields = '__all__'

class CoCurricularActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoCurricularActivity
        fields = '__all__'

class CounsellingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounsellingRecord
        fields = '__all__'

class LeaveLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveLog
        fields = '__all__'

class ProjectDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDetails
        fields = '__all__'
class InternshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = '__all__'

class StudentProfileSerializer(serializers.ModelSerializer):
    parent_details = ParentGuardianDetailsSerializer(read_only=True)
    semesters = AcademicSemesterSerializer(many=True, read_only=True)
    residential_status = ResidentialStatusSerializer(read_only=True)
    disciplinary_actions = DisciplinaryActionSerializer(many=True, read_only=True)
    parent_interactions = ParentInteractionSerializer(many=True, read_only=True)
    cocurricular_activities = CoCurricularActivitySerializer(many=True, read_only=True)
    counselling_records = CounsellingRecordSerializer(many=True, read_only=True)
    leaves = LeaveLogSerializer(many=True, read_only=True)
    projects = ProjectDetailsSerializer(many=True, read_only=True)
    internships = InternshipSerializer(many=True, read_only=True)
    user = CustomUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = StudentProfile
        fields = '__all__'

class StudentRegistrationSerializer(serializers.Serializer):
    # User fields
    username = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    
    # Profile fields (Step 1 & 2)
    name = serializers.CharField()
    roll_no = serializers.CharField()
    department = serializers.CharField()
    batch = serializers.CharField()
    dob = serializers.DateField(required=False, allow_null=True)
    blood_group = serializers.CharField(required=False, allow_blank=True)
    place_of_birth = serializers.CharField(required=False, allow_blank=True)
    degree = serializers.CharField(required=False, default='UG')
    section = serializers.CharField(required=False, allow_blank=True)
    cut_off_marks = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    admission_number = serializers.CharField(required=False, allow_blank=True)
    date_of_joining = serializers.DateField(required=False, allow_null=True)
    contact_number = serializers.CharField(required=False, allow_blank=True)
    
    # Parent details (Step 3) - Flattened for simplicity in the request but nested in DB
    father_name = serializers.CharField(required=False, allow_blank=True)
    father_contact_no = serializers.CharField(required=False, allow_blank=True)
    mother_name = serializers.CharField(required=False, allow_blank=True)
    mother_contact_no = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("Username must be at least 4 characters long.")
        if not value.isalnum():
            raise serializers.ValidationError("Username must only contain letters and numbers.")
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if not value:
            return value
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_roll_no(self, value):
        if CustomUser.objects.filter(roll_no=value).exists():
            raise serializers.ValidationError("A student with this roll number already exists.")
        if StudentProfile.objects.filter(roll_no=value).exists():
            raise serializers.ValidationError("A profile with this roll number already exists.")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not any(not char.isalnum() for char in value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            # 1. Create User
            user = CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data.get('email', ''),
                password=validated_data['password'],
                roll_no=validated_data['roll_no'],
                role='student'
            )
            
            # 2. Create Profile
            profile = StudentProfile.objects.create(
                user=user,
                name=validated_data['name'],
                roll_no=validated_data['roll_no'],
                department=validated_data['department'],
                batch=validated_data['batch'],
                dob=validated_data.get('dob'),
                blood_group=validated_data.get('blood_group', ''),
                place_of_birth=validated_data.get('place_of_birth', ''),
                degree=validated_data.get('degree', 'UG'),
                section=validated_data.get('section', ''),
                cut_off_marks=validated_data.get('cut_off_marks'),
                admission_number=validated_data.get('admission_number', ''),
                date_of_joining=validated_data.get('date_of_joining'),
                contact_number=validated_data.get('contact_number', '')
            )
            
            # 3. Create Parent Details
            ParentGuardianDetails.objects.create(
                student=profile,
                father_name=validated_data.get('father_name', ''),
                father_contact_no=validated_data.get('father_contact_no', ''),
                mother_name=validated_data.get('mother_name', ''),
                mother_contact_no=validated_data.get('mother_contact_no', '')
            )
            
            return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        token['roll_no'] = user.roll_no
        return token
