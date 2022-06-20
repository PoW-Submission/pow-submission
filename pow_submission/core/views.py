import urllib
import json

from django.views.generic import ListView, CreateView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core import models
from users.models import PotentialUser, ADUser, LoginToken
from django import forms
from django.conf import settings
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

    if request.user.is_authenticated and request.user.is_faculty == False:
        termPlans = models.TermPlan.objects.filter(student__email=request.user.email).exclude(plannedWorks=None)
        track = request.user.track
        if track == None:
            return redirect('configure')
        if request.POST.get('message-text'):
            student = request.user
            email_message = '{}  has submitted a question.\n\n{}\n\nLogin: {}'.format(student.email, request.POST.get('message-text'), settings.LOGIN_URL)
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
                    'do_not_reply@app.planofwork-submission.com',
                    emailRecipients,
                    fail_silently=False,
            )
            messages.success(request, 'Your message has been sent.')
    elif request.user.is_authenticated and request.user.is_faculty:
        return redirect('faculty_home')

    else:
        sitekey = settings.GOOGLE_RECAPTCHA_SITE_KEY
        return render(request,
                  'core/home.html',
                  {'sitekey': sitekey})
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
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            ''' Begin reCAPTCHA validation '''
            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                    'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
            }
            data = urllib.parse.urlencode(values).encode()
            req = urllib.request.Request(url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            ''' End reCAPTCHA validation '''

            if result['success']:
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
                    request.session['temp_value'] = userEmail
                    student = ADUser.objects.create_user(email=userEmail, password=None)
                else:
                    student = student[0]

                token = secrets.token_urlsafe(20)
                loginToken = LoginToken.objects.create(user=student, token=token)
                login_url =  '{}/accounts/login?token={}'.format(settings.LOGIN_URL, token)
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
            else:
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return redirect('home')
        elif request.method == 'GET':
            requestToken = request.GET.get('token')
            if requestToken:
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
        form.fields['track'].queryset = models.Track.objects.all().order_by('-term', 'label')
        form.fields['advisor'].queryset = models.Faculty.objects.filter(is_active=True)
        return form
    

@login_required
def faculty_home(request):
    if not (request.user.is_authenticated and request.user.is_faculty):
        return redirect('home')
    students = ADUser.objects.filter(advisor__email=request.user.email)
    if request.user.always_notify:
        students = ADUser.objects.filter(is_faculty=False).filter(track__isnull=False)
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
    if not (request.user.is_authenticated and request.user.is_faculty):
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
        form.fields['track'].queryset = models.Track.objects.all().order_by('-term', 'label')
        form.fields['advisor'].queryset = models.Faculty.objects.filter(is_active=True)
        return form
    


class NewEmailForm(forms.Form):
    email = forms.EmailField()

class NewTerm(forms.Form):
    term_id = forms.CharField()

@login_required
def faculty_term(request, termPlan_id):
    if not (request.user.is_authenticated and request.user.is_faculty):
        return redirect('home')
    termPlan = models.TermPlan.objects.get(pk=termPlan_id)
    currentApproval = termPlan.approval
    currentFirstApproval = termPlan.first_approval
    currentSecondApproval = termPlan.second_approval
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
                if currentApproval == "Approved":
                    messages.error(request, 'Term plan already approved.')
                    return redirect('home')

                if (request.user.email == student.advisor.email):
                    termPlan.first_approval = True
                    termPlan.approval='Submitted'
                    termPlan.save()
                    email_message = '{} has approved term {} for {}.\n\nCourses:\n'.format(student.advisor.name, termPlan.term.label, student.email)
                    plannedWorks = termPlan.plannedWorks.all()
                    for plannedWork in plannedWorks:
                        email_message += plannedWork.course.label + '\n'
                    email_message += '\n\nPlease login to grant final approval: {}/faculty/student_overview/{}/'.format(settings.LOGIN_URL, student.pk)
                    emailRecipients = []
                    adminFaculty = models.ADUser.objects.filter(always_notify=True)
                    for faculty in adminFaculty:
                        emailRecipients.append(faculty.email)
                    send_mail(
                            'Plan of Work Submission',
                            email_message,
                            'do_not_reply@app.planofwork-submission.com',
                            emailRecipients,
                            fail_silently=False,
                    )
                    messages.success(request, 'Term plan approved, and Director of Education notified for final approval.')
                elif (request.user.always_notify):
                    if (currentFirstApproval==False):
                        messages.error(request, 'Advisor must first approve the plan.')
                        return redirect('home')

                    termPlan.first_approval=True
                    termPlan.second_approval=True

                    termPlan.approval = 'Approved'
                    termPlan.save()
                    email_message = 'Your advisor has approved term {}.\n\nCourses:\n'.format(termPlan.term.label)
                    plannedWorks = termPlan.plannedWorks.all()
                    for plannedWork in plannedWorks:
                        email_message += plannedWork.course.label + '\n'
                    #add advisor, maybe everybody
                    email_message += '\n\nLogin: {}'.format(settings.LOGIN_URL)
                    emailRecipients = [student.email]
                    send_mail(
                            'Plan of Work Submission',
                            email_message,
                            'do_not_reply@app.planofwork-submission.com',
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
                email_message = 'Your advisor has denied term {}.\n\nLogin: {}'.format(termPlan.term.label, settings.LOGIN_URL)
                emailRecipients = [student.email]
                send_mail(
                        'Plan of Work Submission',
                        email_message,
                        'do_not_reply@app.planofwork-submission.com',
                        emailRecipients,
                        fail_silently=False,
                )
                messages.success(request, 'Term plan successfully denied.')
            else:
                messages.success(request, 'Term plan successfully saved.')

            return redirect('student_overview', student_id=student.pk)

    form = models.TermPlanForm(instance=termPlan)
    plannedWorks = models.PlannedWork.objects.filter(student=student, termPlan=termPlan.pk)
    term = termPlan.term
    offerings = term.offerings
    defaultCategoryDict = {} 
    for offering in offerings.all():
        course = offering.course
        for category in course.categories.all():
            if category in categories:
                #use course.pk and categor.pk
                defaultCategoryDict[offering.pk] = category.pk
    currentPlans = models.CurrentPlan.objects.filter(termPlan = termPlan.pk)
    return render(request, 
                  'core/faculty_term.html',
                  {'tp': termPlan,
                   'plannedWorks': plannedWorks,
                   'track': track,
                   'categories': categories,
                   'form':form,
                   'defaultCategoryDict':defaultCategoryDict,
                   'currentPlans':currentPlans})

@login_required
def student_term(request, termPlan_id):
    tp = models.TermPlan.objects.get(pk=termPlan_id)
    if not (request.user.is_authenticated and request.user.is_faculty == False and tp.student == request.user):
        return redirect('home')
    saveForm = models.TermPlanForm(request.POST, instance=tp)
    track = request.user.track
    categories = models.Category.objects.filter(track=track)
    if request.method == 'POST':
        #Check to make sure term doesn't have any 'complete' courses
        for plannedWork in tp.plannedWorks.all():
            if plannedWork.completionStatus != None:
                messages.error(request, 'Term Plan already has courses with a completion status.')
                return redirect('home')

        if saveForm.is_valid():
            deleteApproval=True
            saveForm.save(deleteApproval)
            if 'SaveSubmit' in request.POST:
                saveForm.save_submit()

                totalHoursNeeded = track.requiredHours
                submittedHours = 0
                termPlans = models.TermPlan.objects.filter(student=request.user).exclude(plannedWorks=None)
                for termPlan in [x for x in termPlans if (x.approval == 'Approved' or x.approval == 'Submitted')]:
                    for plannedWork in termPlan.plannedWorks.all():
                        submittedHours += plannedWork.course.units

                email_message = '{}  has made a submission for {}.\n{} hours have been submitted or approved out of {} hours needed.\n\nCourses:\n'.format(tp.student.email, tp.term.label, submittedHours, totalHoursNeeded)
                plannedWorks = tp.plannedWorks.all()
                for plannedWork in plannedWorks:
                    email_message += plannedWork.course.label + '\n'
                if request.POST.get("message-text"):
                    email_message += '\nA comment or question has been added to the submission:\n{}'.format(request.POST.get("message-text"))
                email_message += '\n\nLogin to approve submission: {}/faculty/student_overview/{}/'.format(settings.LOGIN_URL, tp.student.pk)
                emailRecipients = []
                #adminFaculty = ADUser.objects.filter(always_notify=True)
                #for faculty in adminFaculty:
                #    emailRecipients.append(faculty.email)
                #if tp.student.advisor.email not in emailRecipients:
                emailRecipients.append(tp.student.advisor.email)
                send_mail(
                        'Plan of Work Submission',
                        email_message,
                        'do_not_reply@app.planofwork-submission.com',
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
    #Add in if the number of terms is zero, send a warning instead of confirmation
    if request.method == 'POST':
        student = models.ADUser.objects.get(pk=student_id)
        if not (request.user.is_authenticated and request.user.is_faculty):
            return redirect('home')
        if (not student.advisor.email == request.user.email and (not request.user.always_notify)):
            return redirect('home')
        termPlans = student.termPlans.all()
        if (request.user.email == student.advisor.email):
            approvedTerms = []
            for termPlan in termPlans:
                if termPlan.approval == 'Submitted' and termPlan.first_approval == False:
                    termPlan.first_approval = True
                    approvedTerms.append(termPlan.term)
                    termPlan.save()

            if len(approvedTerms) == 0:
                messages.error(request, 'No term plans ready for approval.')
                return HttpResponseRedirect(reverse('student_overview', args=(student.pk,)))

            email_message = '{} has approved the following terms for {}.\n\n'.format(student.advisor.name, student.email)
            for term in approvedTerms:
               email_message += term.label + '\n'
            email_message += '\n\nLogin to finalize submission: {}/faculty/student_overview/{}/'.format(settings.LOGIN_URL, student.pk)
            emailRecipients = []
            adminFaculty = models.ADUser.objects.filter(always_notify=True)
            for faculty in adminFaculty:
                emailRecipients.append(faculty.email)
            send_mail(
                    'Plan of Work Submission',
                    email_message,
                    'do_not_reply@app.planofwork-submission.com',
                    emailRecipients,
                    fail_silently=False,
            )
            messages.success(request, 'All submissions successfully approved and sent to Director of Education.')

            return HttpResponseRedirect(reverse('student_overview', args=(student.pk,)))
        elif (request.user.always_notify):
            approvedTerms = []
            for termPlan in termPlans:
                if termPlan.approval == 'Submitted' and termPlan.first_approval:
                    approvedTerms.append(termPlan.term)
                    termPlan.approval = 'Approved'
                    termPlan.save()
                    termPlan.currentPlans.all().delete()
                    for plannedWork in termPlan.plannedWorks.all():
                        currentPlan = models.CurrentPlan(termPlan = termPlan,
                                                course = plannedWork.course,
                                                student=plannedWork.student,
                                                offering=plannedWork.offering)
                        currentPlan.save()

            if len(approvedTerms) == 0:
                messages.error(request, 'No term plans ready for approval.')
                return HttpResponseRedirect(reverse('student_overview', args=(student.pk,)))

            email_message = 'Your advisor has approved the following terms:\n\nLogin:  {}'.format(settings.LOGIN_URL)
            for term in approvedTerms:
                email_message += term.label + '\n'
            emailRecipients = [student.email]
            send_mail(
                    'Plan of Work Submission',
                    email_message,
                    'do_not_reply@app.planofwork-submission.com',
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
        if not (request.user.is_authenticated and request.user.is_faculty):
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

