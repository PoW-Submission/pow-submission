from django.db import models
from django.db.models import Q
from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from users.models import ADUser, PotentialUser
from typedmodels.models import TypedModel


class Course(models.Model):
    label = models.TextField()
    units = models.FloatField()

    def __str__(self):
        return self.label

class Faculty(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    name = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Term(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    label = models.CharField(max_length=50, unique=True)
    courses = models.ManyToManyField(Course, through='Offering')

    def __str__(self):
        return self.label

class Category(models.Model):
    label = models.CharField(max_length=100)
    courses = models.ManyToManyField(Course, related_name='categories', blank=True)

    def __str__(self):
        return self.label

class Offering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, related_name= 'offerings', on_delete=models.CASCADE)
    instructor = models.CharField(max_length=50)
    students = models.ManyToManyField(ADUser, through='PlannedWork')

    def __str__(self):
        return self.course.label

class Track(models.Model):
    label = models.CharField(max_length=100)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, help_text='This is the starting term for the track.')
    categories = models.ManyToManyField(Category, through='TrackRequirement', blank=True)
    courses = models.ManyToManyField(Course,related_name='tracks',  blank=True)
    requiredHours = models.FloatField(default=0)
    program = models.CharField(max_length=20)

    def __str__(self):
        if self.program.upper() == 'PHD' or self.program.upper() == 'MS':
            return self.label + ' (' + self.program + ') ' + ' starting ' + self.term.label
        else:
            return self.label + ' starting ' + self.term.label

class TrackRequirement(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    requiredHours = models.CharField(max_length=100, help_text='Will display as plain text.  You may enter a range such as \'5-6\'')

    def __str__(self):
         return str(self.track) + ' - ' + str(self.category)

class TermPlan(models.Model):
    student = models.ForeignKey(ADUser, related_name = 'termPlans', on_delete=models.CASCADE, blank=True)
    approver = models.CharField(max_length=100, blank=True, unique=False)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, blank=True)
    approval = models.CharField(max_length=20, blank=True)

    def form(self, *args, **kwargs):
        return TermPlanForm(*args, **kwargs)

class PlannedWork(models.Model):
    offering = models.ForeignKey(Offering, null=True, on_delete=models.SET_NULL)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(ADUser, on_delete=models.CASCADE)
    termPlan = models.ForeignKey(TermPlan, related_name='plannedWorks',  on_delete=models.CASCADE)
    grade = models.CharField(max_length=10)
    completionStatus = models.CharField(max_length=20, null=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)

class CurrentPlan(models.Model):
    offering = models.ForeignKey(Offering, null=True, on_delete=models.SET_NULL)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(ADUser, on_delete=models.CASCADE)
    termPlan = models.ForeignKey(TermPlan, related_name='currentPlans',  on_delete=models.CASCADE)

class TermPlanForm(forms.ModelForm):
    class Meta:
        model = TermPlan
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        termPlan = self.instance
        term = termPlan.term
        track = termPlan.student.track
        categories = Category.objects.filter(track=track)
        plannedWorks = PlannedWork.objects.filter(termPlan=termPlan)
        i = -1
        offerings = Offering.objects.filter(term=termPlan.term)
        for i in range( 5):
            fieldName = 'plannedWork_%s' % ( i,)
            categoryName = 'category_%s' % (i,)
            statusName = 'status_%s' % (i,)
            self.fields[fieldName] = forms.ModelChoiceField(queryset=Offering.objects.filter(term=term),
                                                                                             required=False,
                                                            widget=forms.Select(attrs={'class':'w-100'}))

            try:
                self.initial[fieldName] = plannedWorks[i].offering
            except IndexError:
                self.initial[fieldName] = ""

            if i < (len(plannedWorks)) and plannedWorks[i].category:
                self.fields[categoryName] = forms.ModelChoiceField(queryset=categories, required=False,
                                                                    widget=forms.Select(attrs={'class':'w-100'}))
                self.initial[categoryName] = plannedWorks[i].category
            else:
                self.fields[categoryName] = forms.ModelChoiceField(queryset=categories, required=False,
                                                                    widget=forms.Select(attrs={'class':'w-100'}))
                self.initial[categoryName] = ""

            choices=  [('','-------'), ('Passed', 'Passed'), ('Failed', 'Failed'), ('Withdrawn', 'Withdrawn'),] 
            if i < (len(plannedWorks)) and plannedWorks[i].completionStatus:
                self.fields[statusName] = forms.ChoiceField(required=False, choices= choices)
                self.initial[statusName] = plannedWorks[i].completionStatus
            else:
                self.fields[statusName] = forms.ChoiceField(required=False, choices= choices)
                self.initial[statusName] = ""




    def clean(self):
        termPlan = self.instance
        track = termPlan.student.track
        courses = set()
        offerings = set()
        plannedWorks = []
        categories = Category.objects.filter(track=track)
        i = 0
        while i < 5:
          fieldName = 'plannedWork_%s' % (i,)
          categoryName = 'category_%s' % (i,)
          statusName = 'status_%s' % (i,)
          if self.cleaned_data.get(fieldName):
              offering = self.cleaned_data[fieldName]
              if offering in offerings:
                self.add_error(fieldName, 'Duplicate')
              else:
                  offerings.add(offering)
                  if self.cleaned_data.get(statusName):
                      completionStatus = self.cleaned_data[statusName]
                  else:
                      completionStatus = None
                  if self.cleaned_data.get(categoryName):
                      category = self.cleaned_data[categoryName]
                  else:
                      category = None
                      print('category none')
                      for categoryChoice in categories:
                          print('category choice ' + categoryChoice.label)
                          if (categoryChoice in offering.course.categories.all()):
                              print('got it ' + categoryChoice.label)
                              category = categoryChoice
                  plannedWorks.append(PlannedWork(
                      termPlan=termPlan,
                      course=offering.course,
                      student=termPlan.student,
                      offering=offering,
                      category=category,
                      completionStatus=completionStatus
                    ))


          i += 1

        self.cleaned_data["categories"] = categories
        self.cleaned_data["offerings"] = offerings
        self.cleaned_data["plannedWorks"] = plannedWorks
        self.cleaned_data["student"] = termPlan.student
        self.cleaned_data["term"] = termPlan.term

    def save(self, deleteApproval):
        termPlan = self.instance
        termPlan.plannedWorks.all().delete()
        if deleteApproval:
            termPlan.approval = ''
            termPlan.save()
        for plannedWork in self.cleaned_data["plannedWorks"]:
          plannedWork.save()

    def save_submit(self):
        termPlan = self.instance 
        termPlan.approval = "Submitted"
        termPlan.save()

    def hasOfferings(self):
        return self.hasOfferings

    def get_course_fields(self):
        for fieldName in self.fields:
            if fieldName.startswith('plannedWork_'):
                count = fieldName.split("_",1)[1]
                categoryName = 'category_' + count
                statusName = 'status_' + count
                yield [self[fieldName], self[categoryName], self[statusName]]


