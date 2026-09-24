from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomUserViewSet, StudentProfileViewSet, ParentGuardianDetailsViewSet,
    AcademicSemesterViewSet, AcademicCourseViewSet, ResidentialStatusViewSet,
    DisciplinaryActionViewSet, ParentInteractionViewSet, CoCurricularActivityViewSet,
    CounsellingRecordViewSet, LeaveLogViewSet, ProjectDetailsViewSet, InternshipViewSet,
    MyTokenObtainPairView, StudentRegistrationView
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'students', StudentProfileViewSet)
router.register(r'parent-details', ParentGuardianDetailsViewSet)
router.register(r'semesters', AcademicSemesterViewSet)
router.register(r'courses', AcademicCourseViewSet)
router.register(r'residential-status', ResidentialStatusViewSet)
router.register(r'disciplinary-actions', DisciplinaryActionViewSet)
router.register(r'parent-interactions', ParentInteractionViewSet)
router.register(r'cocurricular-activities', CoCurricularActivityViewSet)
router.register(r'counselling-records', CounsellingRecordViewSet)
router.register(r'leaves', LeaveLogViewSet)
router.register(r'projects', ProjectDetailsViewSet)
router.register(r'internships', InternshipViewSet)
router.register(r'register-student', StudentRegistrationView, basename='register-student')

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
