from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from .models import (
    CustomUser, StudentProfile, ParentGuardianDetails, AcademicSemester,
    AcademicCourse, ResidentialStatus, DisciplinaryAction, ParentInteraction,
    CoCurricularActivity, CounsellingRecord, LeaveLog, ProjectDetails, Internship
)
from .serializers import (
    CustomUserSerializer, StudentProfileSerializer, ParentGuardianDetailsSerializer,
    AcademicSemesterSerializer, AcademicCourseSerializer, ResidentialStatusSerializer,
    DisciplinaryActionSerializer, ParentInteractionSerializer, CoCurricularActivitySerializer,
    CounsellingRecordSerializer, LeaveLogSerializer, ProjectDetailsSerializer,
    MyTokenObtainPairSerializer, StudentRegistrationSerializer, InternshipSerializer
)

class StudentRegistrationView(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = StudentRegistrationSerializer
    queryset = CustomUser.objects.none()

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "Student registered successfully"}, status=status.HTTP_201_CREATED)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CustomUser.objects.none()
        
        queryset = CustomUser.objects.all()
        if user.role == 'hod':
            status = self.request.query_params.get('status')
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
            
            role = self.request.query_params.get('role')
            if role:
                queryset = queryset.filter(role=role)
            return queryset
            
        return queryset.filter(id=user.id)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        if request.user.role != 'hod' and not request.user.is_superuser:
            return Response({"detail": "Only HOD/Admin can reset passwords."}, status=status.HTTP_403_FORBIDDEN)
        
        user_to_reset = self.get_object()
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({"error": "new_password is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_to_reset.set_password(new_password)
        user_to_reset.save()
        return Response({"status": f"Password reset for {user_to_reset.username} successfully"})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can deactivate mentors."}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object()
        user.is_active = False
        user.save()
        
        # Automatic Unallocation logic
        unallocated_count = 0
        if user.role == 'mentor':
            students = StudentProfile.objects.filter(mentor=user)
            unallocated_count = students.count()
            students.update(mentor=None)
            
        return Response({
            "status": "success",
            "message": f"User {user.username} deactivated successfully.",
            "unallocated_count": unallocated_count,
            "was_mentor": user.role == 'mentor'
        })

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can activate mentors."}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"status": f"User {user.username} activated successfully."})

    @action(detail=True, methods=['post'], url_path='reassign-students')
    def reassign_students(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can reassign students."}, status=status.HTTP_403_FORBIDDEN)
        
        old_mentor = self.get_object()
        new_mentor_id = request.data.get('new_mentor_id')
        
        if not new_mentor_id:
            return Response({"error": "new_mentor_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_mentor = CustomUser.objects.get(id=new_mentor_id, role='mentor', is_active=True)
            # Find all students assigned to the old mentor
            students = StudentProfile.objects.filter(mentor=old_mentor)
            count = students.count()
            students.update(mentor=new_mentor)
            return Response({"status": f"Successfully reassigned {count} students to {new_mentor.username}."})
        except CustomUser.DoesNotExist:
            return Response({"error": "New mentor not found or is inactive."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='students')
    def mentor_students(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can view mentor students."}, status=status.HTTP_403_FORBIDDEN)
        
        mentor = self.get_object()
        if mentor.role != 'mentor':
            return Response({"error": "User is not a mentor"}, status=status.HTTP_400_BAD_REQUEST)
        
        students = StudentProfile.objects.filter(mentor=mentor)
        serializer = StudentProfileSerializer(students, many=True)
        return Response(serializer.data)

class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StudentProfile.objects.none()
            
        queryset = StudentProfile.objects.all()
        if user.role == 'hod':
            assigned = self.request.query_params.get('assigned')
            if assigned == 'false':
                queryset = queryset.filter(mentor__isnull=True)
            elif assigned == 'true':
                queryset = queryset.filter(mentor__isnull=False)
            
            status = self.request.query_params.get('status')
            if status:
                queryset = queryset.filter(status=status)
            return queryset
            
        elif user.role == 'mentor':
            return queryset.filter(mentor=user)
        elif user.role == 'student':
            return queryset.filter(user=user)
        return queryset.none()

    @action(detail=True, methods=['post'], url_path='assign-mentor')
    def assign_mentor(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can assign mentors."}, status=status.HTTP_403_FORBIDDEN)
        
        student = self.get_object()
        mentor_id = request.data.get('mentor_id')
        
        if not mentor_id:
            student.mentor = None
            student.save()
            return Response({"status": "Student unassigned successfully"})
            
        try:
            mentor = CustomUser.objects.get(id=mentor_id, role='mentor')
            student.mentor = mentor
            student.save()
            return Response({"status": "Mentor assigned successfully"})
        except CustomUser.DoesNotExist:
            return Response({"error": "Mentor not found or user is not a mentor"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        if request.user.role != 'hod':
            return Response({"detail": "Only HOD can update student status."}, status=status.HTTP_403_FORBIDDEN)
        
        student = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['Active', 'Graduated', 'Dropped', 'Transferred']:
            return Response({"error": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)
            
        student.status = new_status
        student.save()
        return Response({"status": f"Student {student.name} status updated to {new_status}."})

class ParentGuardianDetailsViewSet(viewsets.ModelViewSet):
    queryset = ParentGuardianDetails.objects.all()
    serializer_class = ParentGuardianDetailsSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ParentGuardianDetails.objects.none()
        if user.role == 'hod': return ParentGuardianDetails.objects.all()
        if user.role == 'mentor': return ParentGuardianDetails.objects.filter(student__mentor=user)
        return ParentGuardianDetails.objects.filter(student__user=user)

class AcademicSemesterViewSet(viewsets.ModelViewSet):
    queryset = AcademicSemester.objects.all()
    serializer_class = AcademicSemesterSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return AcademicSemester.objects.none()
        if user.role == 'hod': return AcademicSemester.objects.all()
        if user.role == 'mentor': return AcademicSemester.objects.filter(student__mentor=user)
        return AcademicSemester.objects.filter(student__user=user)

class AcademicCourseViewSet(viewsets.ModelViewSet):
    queryset = AcademicCourse.objects.all()
    serializer_class = AcademicCourseSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return AcademicCourse.objects.none()
        if user.role == 'hod': return AcademicCourse.objects.all()
        if user.role == 'mentor': return AcademicCourse.objects.filter(semester__student__mentor=user)
        return AcademicCourse.objects.filter(semester__student__user=user)

class ResidentialStatusViewSet(viewsets.ModelViewSet):
    queryset = ResidentialStatus.objects.all()
    serializer_class = ResidentialStatusSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ResidentialStatus.objects.none()
        if user.role == 'hod': return ResidentialStatus.objects.all()
        if user.role == 'mentor': return ResidentialStatus.objects.filter(student__mentor=user)
        return ResidentialStatus.objects.filter(student__user=user)

class DisciplinaryActionViewSet(viewsets.ModelViewSet):
    queryset = DisciplinaryAction.objects.all()
    serializer_class = DisciplinaryActionSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return DisciplinaryAction.objects.none()
        if user.role == 'hod': return DisciplinaryAction.objects.all()
        if user.role == 'mentor': return DisciplinaryAction.objects.filter(student__mentor=user)
        return DisciplinaryAction.objects.filter(student__user=user)

class ParentInteractionViewSet(viewsets.ModelViewSet):
    queryset = ParentInteraction.objects.all()
    serializer_class = ParentInteractionSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ParentInteraction.objects.none()
        if user.role == 'hod': return ParentInteraction.objects.all()
        if user.role == 'mentor': return ParentInteraction.objects.filter(student__mentor=user)
        return ParentInteraction.objects.filter(student__user=user)

class CoCurricularActivityViewSet(viewsets.ModelViewSet):
    queryset = CoCurricularActivity.objects.all()
    serializer_class = CoCurricularActivitySerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return CoCurricularActivity.objects.none()
        if user.role == 'hod': return CoCurricularActivity.objects.all()
        if user.role == 'mentor': return CoCurricularActivity.objects.filter(student__mentor=user)
        return CoCurricularActivity.objects.filter(student__user=user)

class CounsellingRecordViewSet(viewsets.ModelViewSet):
    queryset = CounsellingRecord.objects.all()
    serializer_class = CounsellingRecordSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return CounsellingRecord.objects.none()
        if user.role == 'hod': return CounsellingRecord.objects.all()
        if user.role == 'mentor': return CounsellingRecord.objects.filter(student__mentor=user)
        return CounsellingRecord.objects.filter(student__user=user)

class LeaveLogViewSet(viewsets.ModelViewSet):
    queryset = LeaveLog.objects.all()
    serializer_class = LeaveLogSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return LeaveLog.objects.none()
        if user.role == 'hod': return LeaveLog.objects.all()
        if user.role == 'mentor': return LeaveLog.objects.filter(student__mentor=user)
        return LeaveLog.objects.filter(student__user=user)

class ProjectDetailsViewSet(viewsets.ModelViewSet):
    queryset = ProjectDetails.objects.all()
    serializer_class = ProjectDetailsSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ProjectDetails.objects.none()
        if user.role == 'hod': return ProjectDetails.objects.all()
        if user.role == 'mentor': return ProjectDetails.objects.filter(student__mentor=user)
        return ProjectDetails.objects.filter(student__user=user)
class InternshipViewSet(viewsets.ModelViewSet):
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return Internship.objects.none()
        if user.role == 'hod': return Internship.objects.all()
        if user.role == 'mentor': return Internship.objects.filter(student__mentor=user)
        return Internship.objects.filter(student__user=user)
