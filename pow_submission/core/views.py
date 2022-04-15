from django.views.generic import ListView, CreateView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core import models
from users.models import PotentialUser, ADUser, LoginToken
from django import forms
from django.urls import reverse
from django.template.defaulttags import register
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import secrets

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)

# Create your views here.
def home_view(request):
    consent_forms = []

    if request.user.is_authenticated and request.user.is_staff == False:
        termPlans = models.TermPlan.objects.filter(student__email=request.user.email).exclude(plannedWorks=None)
        track = request.user.track
        if track == None:
            return redirect('configure')
        if request.POST.get('message-text'):
            student = request.user
            email_message = '{}  has submitted a question.\n\n{}'.format(student.email, request.POST.get('message-text'))
            #double check who should receive question
            emailRecipients = []
            adminFaculty = models.ADUser.objects.filter(always_notify=True)
            for faculty in adminFaculty:
                emailRecipients.append(faculty.email)
            if student.advisor.email not in emailRecipients:
                emailRecipients.append(student.advisor.email)
            send_mail(
                    'Plan of Work Submission - Help Request',
                    email_message,
                    'login_retrieval@app.planofwork-submission.com',
                    emailRecipients,
                    fail_silently=False,
            )
            messages.success(request, 'Your message has been sent.')
    elif request.user.is_authenticated and request.user.is_staff:
        return redirect('faculty_home')

    else:
        return render(request,
                  'core/home.html',)
    categories = models.Category.objects.filter(track=track)
    categoryDicts = []
    for category in categories:
        approvedHours = 0
        for termPlan in [x for x in termPlans if x.approval == 'Approved']:
            for plannedWork in termPlan.plannedWorks.all():
                if category == plannedWork.category:
                    approvedHours += plannedWork.course.units
        trackRequirement = models.TrackRequirement.objects.get(category=category, track=track)
        categoryDicts.append({'category':category, 'hours':(int)(approvedHours), 'requiredHours':(trackRequirement.requiredHours)})
    termPlanDicts = []
    for termPlan in termPlans:
        hours = 0
        for plannedWork in termPlan.plannedWorks.all():
            hours += plannedWork.course.units
        termPlanDicts.append({'termPlan':termPlan, 'hours':(int)(hours)})
    terms = []
    terms = models.Term.objects.all()
    return render(request,
                  'core/home.html',
                  {'termPlans': termPlans,
                   'termPlanDicts': termPlanDicts,
                   'terms': terms,
                   'track': track,
                   'categories': categories,
                   'categoryDicts':categoryDicts})

def login_view(request):
    print('login time')
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            userEmail = request.POST.get('username')
            try:
                validate_email(userEmail)
            except ValidationError as e:
                print("bad email, details:", e)
                return redirect('home')
                
            domain = userEmail[-9:]
            if domain.lower() != '@uams.edu':
                #add error message
                return redirect('home')
            student = ADUser.objects.filter(email=userEmail)
            if not student:
                student = ADUser.objects.create_user(email=userEmail, password=None)
            else:
                student = student[0]

            token = secrets.token_urlsafe(20)
            loginToken = LoginToken.objects.create(user=student, token=token)
            login_url =  'http://localhost:8000/accounts/login?token={}'.format(token)
            email_message = "Here is your login URL for Plan of Work Submission\n\n{}".format(login_url)
            send_mail(
                    'Plan of Work Submission',
                    email_message,
                    'login_retrieval@app.planofwork-submission.com',
                    [userEmail],
                    fail_silently=False,
            )
            return render(request,
                          'registration/login.html',
                          {})
        elif request.method == 'GET':
            requestToken = request.GET.get('token')
            if requestToken:
                print(requestToken)
                user = authenticate(request, token=requestToken)
                if user is not None:
                    login(request, user)
                    return redirect('home')
            return redirect('home')




class configure(UpdateView): 
    model = ADUser
    fields = ('track', 'advisor',)
    template_name = 'core/configure.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, *kwargs)
        else:
            return redirect('home')

    def get_object(self):
        return get_object_or_404(ADUser, pk=self.request.user.pk)
    
    def get_success_url(self):
        messages.success(self.request, 'Your changes have been saved.')
        return reverse('home',)
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['advisor'].queryset = models.Faculty.objects.filter(is_active=True)
        return form
    

@login_required
def faculty_home(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('home')
    students = ADUser.objects.filter(advisor__email=request.user.email)
    if request.user.always_notify:
        students = ADUser.objects.filter(is_staff=False).filter(track__isnull=False)
    for student in students:
        approvedHours = 0
        submissionsPending = False
        termPlans = student.termPlans.all()
        for termPlan in termPlans:
            if termPlan.approval == "Approved":
                plannedWorks = termPlan.plannedWorks.all()
                for plannedWork in plannedWorks:
                    approvedHours += plannedWork.course.units
            elif termPlan.approval == 'Submitted':
                    submissionsPending = True
        student.approvedHours = int(approvedHours)
        student.submissionsPending = submissionsPending
    return render(request,
                  'core/faculty_home.html',
                  {'students': students})
@login_required
def student_overview(request, student_id):
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('home')
    student = ADUser.objects.get(pk=student_id)
    if (not student.advisor.email == request.user.email and (not request.user.always_notify)):
      return redirect('home')
    termPlans = models.TermPlan.objects.filter(student=student).exclude(plannedWorks=None)
    track = student.track
    categories = models.Category.objects.filter(track=track)

    categoryDicts = []
    for category in categories:
        approvedHours = 0
        for termPlan in [x for x in termPlans if x.approval == 'Approved']:
            for plannedWork in termPlan.plannedWorks.all():
                if category == plannedWork.category:
                    approvedHours += plannedWork.course.units
        trackRequirement = models.TrackRequirement.objects.get(category=category, track=track)
        categoryDicts.append({'category':category, 'hours':(int)(approvedHours), 'requiredHours':(trackRequirement.requiredHours)})
    termPlanDicts = []
    for termPlan in termPlans:
        hours = 0
        for plannedWork in termPlan.plannedWorks.all():
            hours += plannedWork.course.units
        termPlanDicts.append({'termPlan':termPlan, 'hours':(int)(hours)})
    terms = []
    terms = models.Term.objects.all()
    return render(request,
                  'core/student_overview.html',
                  {'termPlans': termPlans,
                   'student': student,
                   'termPlanDicts': termPlanDicts,
                   'terms': terms,
                   'track': track,
                   'categories': categories,
                   'categoryDicts':categoryDicts})

class faculty_configure(UpdateView): 
    model = ADUser
    fields = ('track', 'advisor',) 
    template_name = 'core/faculty_configure.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            student = models.ADUser.objects.get(pk=self.kwargs['student_id'])
            if (not student.advisor.email == request.user.email and (not request.user.always_notify)):
                return redirect('home')
            return super().dispatch(request, *args, *kwargs)
        else:
            return redirect('home')

    def get_object(self):
        return get_object_or_404(ADUser, pk=self.kwargs['student_id'])
    
    def get_success_url(self):
        messages.success(self.request, 'Your changes have been saved.')
        return reverse('home',)
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['advisor'].queryset = models.Faculty.objects.filter(is_active=True)
        return form
    


class NewEmailForm(forms.Form):
    email = forms.EmailField()

class NewTerm(forms.Form):
    term_id = forms.CharField()

@login_required
def faculty_term(request, termPlan_id):
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('home')
    termPlan = models.TermPlan.objects.get(pk=termPlan_id)
    student = termPlan.student
    if (not student.advisor.email == request.user.email and (not request.user.always_notify)):
      return redirect('home')
    saveForm = models.TermPlanForm(request.POST, instance=termPlan)
    track = student.track
    categories = models.Category.objects.filter(track=track)
    if request.method == 'POST':
        if saveForm.is_valid():
            deleteApproval = False
            saveForm.save(deleteApproval)
            if 'ApproveButton' in request.POST:
                termPlan.approval = 'Approved'
                termPlan.save()
                email_message = 'Your advisor has approved term {}.'.format(termPlan.term.label)
                emailRecipients = [student.email]
                send_mail(
                        'Plan of Work Submission',
                        email_message,
                        'login_retrieval@app.planofwork-submission.com',
                        emailRecipients,
                        fail_silently=False,
                )

                termPlan.currentPlans.all().delete()
                for plannedWork in termPlan.plannedWorks.all():
                    currentPlan = models.CurrentPlan(termPlan = termPlan,
                                            course = plannedWork.course,
                                            student=plannedWork.student,
                                            offering=plannedWork.offering)
                    currentPlan.save()
                messages.success(request, 'Term plan successfully approved.')
            elif 'DenyButton' in request.POST:
                termPlan.approval = 'Denied'
                termPlan.save()
                email_message = 'Your advisor has denied term {}.'.format(termPlan.term.label)
                emailRecipients = [student.email]
                send_mail(
                        'Plan of Work Submission',
                        email_message,
                        'login_retrieval@app.planofwork-submission.com',
                        emailRecipients,
                        fail_silently=False,
                )
                messages.success(request, 'Term plan successfully denied.')
            else:
                messages.success(request, 'Term plan successfully saved.')

            return redirect('student_overview', student_id=student.pk)

    form = models.TermPlanForm(instance=termPlan)
    plannedWorks = models.PlannedWork.objects.filter(student=student, termPlan=termPlan.pk)
    return render(request, 
                  'core/faculty_term.html',
                  {'tp': termPlan,
                   'plannedWorks': plannedWorks,
                   'track': track,
                   'categories': categories,
                   'form':form})

@login_required
def student_term(request, termPlan_id):
    tp = models.TermPlan.objects.get(pk=termPlan_id)
    if not (request.user.is_authenticated and request.user.is_staff == False and tp.student == request.user):
        return redirect('home')
    saveForm = models.TermPlanForm(request.POST, instance=tp)
    track = request.user.track
    categories = models.Category.objects.filter(track=track)
    print('categories here ')
    for category in categories:
        print (category.label)
    if request.method == 'POST':
        #Check to make sure term doesn't have any 'complete' courses
        if saveForm.is_valid():
            deleteApproval=True
            saveForm.save(deleteApproval)
            if 'SaveSubmit' in request.POST:
                saveForm.save_submit()

                totalHoursNeeded = 0
                trackRequirements = models.TrackRequirement.objects.filter(track=track)
                for trackRequirement in trackRequirements:
                    totalHoursNeeded += trackRequirement.requiredHours
                submittedHours = 0
                termPlans = models.TermPlan.objects.filter(student=request.user).exclude(plannedWorks=None)
                for termPlan in [x for x in termPlans if (x.approval == 'Approved' or x.approval == 'Submitted')]:
                    for plannedWork in termPlan.plannedWorks.all():
                        submittedHours += plannedWork.course.units
                        print(plannedWork.course)

                email_message = '{}  has made a submission for {}.\n{} hours have been submitted or approved out of {} hours needed.'.format(tp.student.email, tp.term.label, submittedHours, totalHoursNeeded)
                if request.POST.get("message-text"):
                    email_message += '\n\nA comment or question has been added to the submission:\n{}'.format(request.POST.get("message-text"))
                emailRecipients = []
                adminFaculty = ADUser.objects.filter(always_notify=True)
                for faculty in adminFaculty:
                    emailRecipients.append(faculty.email)
                if tp.student.advisor.email not in emailRecipients:
                    emailRecipients.append(tp.student.advisor.email)
                send_mail(
                        'Plan of Work Submission',
                        email_message,
                        'login_retrieval@app.planofwork-submission.com',
                        emailRecipients,
                        fail_silently=False,
                )
                messages.success(request, 'Term Plan saved and submitted.  An email has been sent to your advisor for approval.')
            else:
                messages.success(request, 'Your term plan has been saved.')
            return redirect('home')
        else:
            print(saveForm.errors)
    tp = models.TermPlan.objects.get(pk=termPlan_id)
    form = models.TermPlanForm(instance=tp)
    plannedWorks = models.PlannedWork.objects.filter(student=tp.student, termPlan=tp.pk)
    tp.hasComplete = False
    for plannedWork in plannedWorks:
        if not plannedWork.completionStatus == None:
            tp.hasComplete = True
    return render(request, 
                  'core/student_term.html',
                  {'tp': tp,
                   'plannedWorks': plannedWorks,
                   'track': track,
                   'categories': categories,
                   'form': form})

@login_required
def approve_all(request, student_id):
    if request.method == 'POST':
        student = models.ADUser.objects.get(pk=student_id)
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect('home')
        if (not student.advisor.email == request.user.email and (not request.user.always_notify)):
            return redirect('home')
        termPlans = student.termPlans.all()
        for termPlan in termPlans:
            if termPlan.approval == 'Submitted':
                termPlan.approval = 'Approved'
                termPlan.save()
                termPlan.currentPlans.all().delete()
                for plannedWork in termPlan.plannedWorks.all():
                    currentPlan = models.CurrentPlan(termPlan = termPlan,
                                            course = plannedWork.course,
                                            student=plannedWork.student,
                                            offering=plannedWork.offering)
                    currentPlan.save()

        email_message = 'Your advisor has approved all submitted term plans.'
        emailRecipients = [student.email]
        send_mail(
                'Plan of Work Submission',
                email_message,
                'login_retrieval@app.planofwork-submission.com',
                emailRecipients,
                fail_silently=False,
        )
        messages.success(request, 'All submissions successfully approved.')

        return HttpResponseRedirect(reverse('student_overview', args=(student.pk,)))
    else:
        return HttpResponse("require POST", status=405)

@login_required
def faculty_approve(request, termPlan_id, approval_type):
    if request.method == 'POST':
        termPlan = models.TermPlan.objects.get(pk=termPlan_id)
        student = termPlan.student
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect('home')
        if not student.advisor.email == request.user.email:
        #add - and request.user.email not in (3 admin faculty)
            return redirect('home')
        if approval_type == 'A':
            termPlan.approval = 'Approved'
            termPlan.save()
        elif approval_type == 'TA':
            termPlan.approval = 'Temp Approved'
            termPlan.save()

        if approval_type == 'A' or approval_type == 'TA':
            termPlan.currentPlans.all().delete()
            for plannedWork in termPlan.plannedWorks.all():
                    currentPlan = models.CurrentPlan(termPlan = termPlan,
                                            course = plannedWork.course,
                                            student=plannedWork.student,
                                            offering=plannedWork.offering)
                    currentPlan.save()
            


        return HttpResponseRedirect(reverse('student_overview', args=(student.pk,)))
    else:
        return HttpResponse("require POST", status=405)

@login_required
def new_term(request):
    if not request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = NewTerm(request.POST)
        if form.is_valid():
            term_id = form.cleaned_data['term_id']
            term = models.Term.objects.get(pk=term_id)
            email = request.user.email
            student = models.ADUser.objects.get(email=email)
            
            termPlans = models.TermPlan.objects.filter(student=student, term=term)
            for termPlan in termPlans:
                if termPlan.plannedWorks.count() > 0:
                    messages.error(request, 'Term has already been created.')
                    return redirect('home')
                
            termPlan = models.TermPlan.objects.create(student=student, term=term)
            termPlan.save()
            return HttpResponseRedirect(reverse('student_term', args=(termPlan.pk,)))
        else:
            messages.error(request, 'An error has occurred.  Please try again.  If the problem persists, please use the help link at the bottom of the page.')
            return redirect('home')
    else:
        return HttpResponse("require POST", status=405)

