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
    print('here we are')
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
            adminFaculty = ADUser.objects.filter(always_notify=True)
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
        categoryDicts.append({'category':category, 'hours':(int)(approvedHours)})
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
    
    @login_required
    def configure(request):
        if request.user.is_authenticated:
            return render(requst,
                    'core/configure.html',
                    )
        else:
            return redirect('home')


#    student = ADUser.objects.get(email=request.user.email)
#    return render(request,
#                  'core/configure.html',
#                  {'student': student})

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
        categoryDicts.append({'category':category, 'hours':(int)(approvedHours)})
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

class NewEmailForm(forms.Form):
    email = forms.EmailField()

@login_required
def form_manage(request, form_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    form = NewEmailForm()
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return redirect('home')
    if request.method == 'POST':
        form = NewEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            pu, created = PotentialUser.objects.get_or_create(email=email)
            if not cf.authorized_users.filter(email=email).exists():
                cf.authorized_users.add(pu)
                cf.save()
                form = NewEmailForm()
    return render(request,
                  'core/form_manage.html',
                  {'cf': cf,
                   'form': form})

@login_required
def form_manage_delete(request, form_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    form = NewEmailForm()
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return redirect('home')
    if request.method == 'POST':
        form = NewEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            id = PotentialUser.objects.get(email=email)
            cf.authorized_users.remove(id)
            return redirect('form_manage', cf.id)
    return render(request,
                  'core/form_manage.html',
                  {'cf': cf,
                   'form': form})

class NewConsentForm(forms.Form):
    study_name = forms.CharField()

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

                email_message = '{}  has made a submission for {}.\n\n{} hours have been submitted or approved out of {} hoursneeded.'.format(tp.student.email, tp.term.label, submittedHours, totalHoursNeeded)
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
def form_main(request, form_id, section_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return redirect('home')
    sections = models.Section.objects.all()
    section = models.Section.objects.get(pk=section_id)
    next_section = None
    is_next = False
    for sec in sections:
        if is_next:
            next_section = sec.pk
            break
        if sec.pk == section.pk:
            is_next = True
    if next_section is None:
        next_section = sections.first().pk

    pd = cf.print_dictionary
    qgroups = list(filter(lambda x: x.enabled(pd),
                         models.QGroup.objects.filter(section=section)))

    response_text = []

    for qgroup in qgroups:
        qgroup.qs = qgroup.questions.all()
        for question in qgroup.qs:
            try:
                r = models.Response.objects.get(form=cf, question=question)
                question.form = question.form(r.data)

                try:
                    et = models.EditText.objects.get(response=r)
                    question.edit_text = et
                except:
                    question.edit_text = None

                # there is a response do some things
                # Check if canned text exists, add that
                if(models.EditText.objects.filter(response=r).exists()):
                    response_text.append(models.EditText.objects.get(response=r).text)
                elif question.type == 'core.freetextquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.yesnoexplainquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.textlistquestion':
                    text_list = []
                    for line in question.for_dict(r.data):
                        if(line != ""):
                            text_list.append(f"<li>{line}</li>")
                    response_text.append(f"<ul>{' '.join(text_list)}</li>")
                else:
                    pass
            except:
                question.form = question.form()
    return render(request,
                  'core/form.html',
                  {'consent_form': cf,
                   'pd': pd,
                   'section': section,
                   'sections': sections,
                   'next_section': next_section,
                   'qgroups': qgroups,
                   'response_text': response_text})

@login_required
def section_preview(request, form_id, section_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return HttpResponse("")
    section = models.Section.objects.get(pk=section_id)
    pd = cf.print_dictionary
    qgroups = list(filter(lambda x: x.enabled(pd),
                         models.QGroup.objects.filter(section=section)))

    response_text = []

    for qgroup in qgroups:
        qgroup.qs = qgroup.questions.all()
        for question in qgroup.qs:
            try:
                r = models.Response.objects.get(form=cf, question=question)
                # there is a response do some things
                # Check if canned text exists, add that
                if(models.EditText.objects.filter(response=r).exists()):
                    response_text.append(models.EditText.objects.get(response=r).text)
                elif question.type == 'core.freetextquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.yesnoexplainquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.textlistquestion':
                    text_list = []
                    for line in question.for_dict(r.data):
                        if(line != ""):
                            text_list.append(f"<li>{line}</li>")
                    response_text.append(f"<ul>{' '.join(text_list)}</li>")
                else:
                    pass
            except:
                question.form = question.form()
    if(section.template == 'none'):
        return HttpResponse("")
    return render(request,
                  section.template,
                  {'pd': pd,
                   'response_text': response_text})


@login_required
def form_sections(request, form_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return redirect('home')
    sections = models.Section.objects.all()
    return render(request,
                  'core/form_sections.html',
                  {'consent_form': cf,
                   'sections': sections})

def form_print(request, form_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    pd = models.ConsentForm.objects.get(pk=form_id).print_dictionary
    qgroups = list(filter(lambda x: x.enabled(pd),
                         models.QGroup.objects.all()))

    response_text = []

    for qgroup in qgroups:
        qgroup.qs = qgroup.questions.all()
        for question in qgroup.qs:
            try:
                r = models.Response.objects.get(form=cf, question=question)
                question.form = question.form(r.data)

                try:
                    et = models.EditText.objects.get(response=r)
                    question.edit_text = et
                except:
                    question.edit_text = None

                # there is a response do some things
                # Check if canned text exists, add that
                if(models.EditText.objects.filter(response=r).exists()):
                    response_text.append(models.EditText.objects.get(response=r).text)
                elif question.type == 'core.freetextquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.yesnoexplainquestion':
                    response_text.append(question.for_dict(r.data))
                elif question.type == 'core.textlistquestion':
                    text_list = []
                    for line in question.for_dict(r.data):
                        if(line != ""):
                            text_list.append(f"<li>{line}</li>")
                    response_text.append(f"<ul>{' '.join(text_list)}</li>")
                else:
                    pass
            except:
                question.form = question.form()
    return render(request,
                  'core/print_form.html',
                  {'pd': pd, 'response_text': response_text})

@login_required
def new_form(request):
    if request.method == 'POST':
        form = NewConsentForm(request.POST)
        if form.is_valid():
            study_name = form.cleaned_data['study_name']
            email = request.user.email
            pu, created = PotentialUser.objects.get_or_create(email=email)
            cf = models.ConsentForm.objects.create(study_name=study_name)
            cf.authorized_users.add(pu)
            cf.save()
            return HttpResponseRedirect(reverse('form_sections', args=(cf.pk,)))
        else:
            return HttpResponse("bad form", status=500)
    else:
        return HttpResponse("require POST", status=405)

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
            return HttpResponse("bad form", status=500)
    else:
        return HttpResponse("require POST", status=405)

@login_required
def question_main(request, form_id, question_id):
    if request.method == 'POST':
        question = models.Question.objects.get(pk=question_id)
        cf = models.ConsentForm.objects.get(pk=form_id)
        form = question.form(request.POST)
        if form.is_valid():
            r, created = models.Response.objects.get_or_create(form=cf,
                                                      question=question)
            r.data = form.cleaned_data
            r.save()
            if(question.canned_yes):
                et, created = models.EditText.objects.get_or_create(response=r)
                et.text = question.canned_yes.text
                et.save()
            if(question.canned_no):
                et, created = models.EditText.objects.get_or_create(response=r)
                et.text = question.canned_no.text
                et.save()
            return HttpResponse("ok", status=200)
        else:
            return HttpResponse("bad form", status=500)
    return HttpResponse("require POST", status=405)

@login_required
def edit_text_edit(request, form_id, question_id):
    if request.method == 'POST':
        question = models.Question.objects.get(pk=question_id)
        cf = models.ConsentForm.objects.get(pk=form_id)
        r = models.Response.objects.get(form=cf, question=question)
        if('text' in request.POST):
            text = request.POST["text"]
            et = models.EditText.objects.get(response=r)
            et.text = text
            et.save()
            return HttpResponse("ok", status=200)
        else:
            return HttpResponse("missing text", status=500)
    return HttpResponse("require POST", status=405)


@login_required
def debug_questions(request):
    questions = models.Question.objects.all()
    sections = models.Section.objects.all()
    qgroups = models.QGroup.objects.all()
    for qgroup in qgroups:
        qgroup.qs = qgroup.questions.all()
    for question in questions:
        question.warn = False
        question.in_group = False
        for qg in qgroups:
            if question in qg.qs.all():
                if question.in_group == False:
                    question.in_group = qg.name
                else:
                    question.warn = True
                    question.in_group = "MULTIPLE GROUPS {} {}".format(question.in_group, qg.name)
    return render(request, 'core/debug_questions.html',
                    {'questions': questions,
                     'sections': sections,
                     'qgroups': qgroups})

@login_required
def debug_json(request, form_id):
    cf = models.ConsentForm.objects.get(pk=form_id)
    if not cf.authorized_users.filter(email=request.user.email).exists():
        return redirect('home')
    pd = cf.print_dictionary
    return JsonResponse(pd)
