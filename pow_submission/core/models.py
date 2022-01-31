from django.db import models
from django.db.models import Q
from django import forms
from users.models import ADUser, PotentialUser
from typedmodels.models import TypedModel

class ConsentForm(models.Model):
    study_name = models.CharField(max_length=500)
    @property
    def print_dictionary(self):
        dict = {}
        for question in Question.objects.all():
            try:
                response = Response.objects.get(form=self, question=question)
                dict[question.label] = question.for_dict(response.data)
            except Response.DoesNotExist:
                pass
        return dict
    def __str__(self):
        return self.study_name[:20]

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
    label = models.CharField(max_length=50, unique=True)
    courses = models.ManyToManyField(Course, through='Offering')

    def __str__(self):
        return self.label

class Offering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, related_name= 'offerings', on_delete=models.CASCADE)
    instructor = models.CharField(max_length=50)
    students = models.ManyToManyField(ADUser, through='PlannedWork')

    def __str__(self):
        return self.course.label

class Category(models.Model):
    label = models.CharField(max_length=100)
    courses = models.ManyToManyField(Course, related_name='categories', blank=True)

    def __str__(self):
        return self.label

class Track(models.Model):
    label = models.CharField(max_length=100, unique=True)
    startTerm = models.ForeignKey(Term, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category, blank=True)
    courses = models.ManyToManyField(Course,related_name='tracks',  blank=True)

    def __str__(self):
         return self.label

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
        track = termPlan.student.track
        categories = Category.objects.filter(track=track)
        plannedWorks = PlannedWork.objects.filter(termPlan=termPlan)
        for category in categories:
            i = -1
            plannedWorksByCategory = [x for x in plannedWorks if category in x.course.categories.all()] 
            offerings = Offering.objects.filter(term=termPlan.term)
            for i in range(max(len(plannedWorksByCategory), 4) ):
                fieldName = 'plannedWork_%s_%s' % (category.label, i,)
                checkboxName = 'replaceWith_%s_%s' % (category.label, i,)
                offeringName = 'offering_%s_%s' % (category.label, i,)
                criterion1 = Q(tracks__in=[track])
                criterion2 = Q(categories__in=[category])
                self.fields[fieldName] = forms.ModelChoiceField(queryset=Course.objects.filter(criterion1 & criterion2),
                                                                                                 required=False,
                                                                widget=forms.Select(attrs={'class':'w-100'}))

                try:
                    self.initial[fieldName] = plannedWorksByCategory[i].course
                except IndexError:
                    self.initial[fieldName] = ""

                offerings = Offering.objects.filter(term=termPlan.term)
                self.hasOfferings = False
                if offerings:
                  self.hasOfferings = True
                  if i < (len(plannedWorksByCategory)) and plannedWorksByCategory[i].offering:
                      self.fields[offeringName] = forms.ModelChoiceField(queryset=offerings,
                             required=False,
                             widget=forms.Select(attrs={'class':'w-100'}))
                      self.initial[offeringName] = plannedWorksByCategory[i].offering
                      self.fields[checkboxName] = forms.BooleanField(initial=True, required=False)
                  else:
                      self.fields[offeringName] = forms.ModelChoiceField(queryset=offerings,
                             required=False,
                             widget=forms.Select(attrs={'class':'w-100'}))
                      self.initial[offeringName] = ""
                      self.fields[checkboxName] = forms.BooleanField(initial=False, required=False)




        #create an extra blank field
        #fieldName = 'plannedWork_offering_%s' % (i + 1,)
        #self.fields[fieldName] = forms.ModelChoiceField(queryset=Offering.objects.filter(term=termPlan.term), 
         #                                               widget=forms.Select(attrs={'class':'blankOffering'}),
          #                                              required=False)

    def clean(self):
        termPlan = self.instance
        track = termPlan.student.track
        courses = set()
        plannedWorks = []
        categories = Category.objects.filter(track=track)
        for category in categories:
            i = 0
            while i < 4:
              fieldName = 'plannedWork_%s_%s' % (category.label, i,)
              checkboxName = 'replaceWith_%s_%s' % (category.label, i,)
              offeringName = 'offering_%s_%s' % (category.label, i,)
              
              if self.cleaned_data.get(fieldName):
                  course = self.cleaned_data[fieldName]
                  if course in courses:
                       self.add_error(fieldName, 'Duplicate')	
                  else:
                       courses.add(course)
                       if self.cleaned_data.get(checkboxName):
                         self.cleaned_data.get(offeringName)
                         offering = self.cleaned_data[offeringName]
                       else:
                         offering = None
                       plannedWorks.append(PlannedWork(
                         termPlan=termPlan,
                         course=course,
                         student=termPlan.student,
                         offering=offering,
                       ))
                      
                       
              i += 1
        self.cleaned_data["courses"] = courses
        self.cleaned_data["plannedWorks"] = plannedWorks
        self.cleaned_data["student"] = termPlan.student
        self.cleaned_data["term"] = termPlan.term

    def save(self):
        termPlan = self.instance
        termPlan.plannedWorks.all().delete()
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
                if self.hasOfferings:
                  checkboxName = 'replaceWith_' + count
                  offeringName = 'offering_' + count
                  yield [self[fieldName], self[checkboxName], self[offeringName]]
                else: 
                  yield [self[fieldName], None, None]


class CannedText(models.Model):
    label = models.CharField(max_length=50, unique=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.label

class Question(TypedModel):
    text = models.TextField(blank=True)
    extra_text = models.TextField(blank=True)
    order = models.FloatField(unique=True)
    label = models.CharField(max_length=50, unique=True)
    canned_yes = models.ForeignKey(CannedText, on_delete=models.CASCADE, blank=True, null=True, related_name="canned_yes")
    canned_no = models.ForeignKey(CannedText, on_delete=models.CASCADE, blank=True, null=True, related_name="canned_no")

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']

class Response(models.Model):
    form = models.ForeignKey(ConsentForm, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    data = models.JSONField(blank=True, null=True)
    class Meta:
        unique_together = [['form', 'question']]
    def __str__(self):
        return "{}[{}]".format(self.form, self.question)

class EditText(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    text = models.TextField(blank=True)

    def __str__(self):
        return "et [{}]".format(self.response)

class Section(models.Model):
    name = models.TextField()
    order = models.FloatField(unique=True)
    template = models.TextField()

    def current_count(self):
        return "{} / {}".format('?', '?')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

class QGroup(models.Model):
    name = models.TextField(blank=True)
    order = models.FloatField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, blank=True)
    logic = models.TextField(default='True')

    def __str__(self):
        return self.name

    def enabled(self, pd):
        try:
            ret = eval(self.logic, {'pd': pd})
            return ret
        except:
            return False

    class Meta:
        ordering = ['order']
        unique_together = ['order', 'section']

class YesNoForm(forms.Form):
    yes = forms.TypedChoiceField(label='',
                             required=True,
                             coerce=lambda x: x == 'True',
                             choices=[(True, 'Yes'),(False, 'No')],
                             widget=forms.RadioSelect)

class YesNoQuestion(Question):
    def form(self, *args, **kwargs):
        return YesNoForm(*args, **kwargs)
    def for_dict(self, data):
        return data['yes']

class YesNoExplainForm(forms.Form):
    yes = forms.TypedChoiceField(label='',
                             required=True,
                             coerce=lambda x: x == 'True',
                             choices=[(True, 'Yes'),(False, 'No')],
                             widget=forms.RadioSelect(attrs={'data-yesno-target': 'yesno',
                                                             'data-action': 'input->yesno#toggled'}))
    hidden = {'hidden': None, 'data-yesno-target': 'explain', 'placeholder': 'Explain...'}
    explanation = forms.CharField(label='', required=False, widget=forms.Textarea(attrs=hidden), help_text='Please Explain')
    def __init__(self, help_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['explanation'].help_text = help_text



class YesNoExplainQuestion(Question):
    YNB_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
        ('B', 'Both')
    ]
    explain_when = models.CharField(blank=True, null=True, max_length=1, choices=YNB_CHOICES)
    def form(self, *args, **kwargs):
        return YesNoExplainForm(self.extra_text, *args, **kwargs)
    def for_dict(self, data):
        return data['explanation']

class FreeTextForm(forms.Form):
    text = forms.CharField(label='', required=True, widget=forms.Textarea(attrs={'class': 'form-control'}))

class FreeTextQuestion(Question):
    def form(self, *args, **kwargs):
        return FreeTextForm(*args, **kwargs)
    def for_dict(self, data):
        return data['text']

class MultiSelectForm(forms.Form):
    options = forms.MultipleChoiceField(label='', widget=forms.CheckboxSelectMultiple)
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = zip(range(len(choices)), choices)
        self.fields['options'].choices = c
        self.empty_permitted = True

class MultiSelectQuestion(Question):
    options = models.JSONField(null=True, blank=True)
    def form(self, *args, **kwargs):
        return MultiSelectForm(self.options, *args, **kwargs)

    def for_dict(self, data):
        ret = []
        if('options' not in data.keys()):
            return ret
        for i in data['options']:
            ret.append(self.options[int(i)])
        return ret

class TextListingForm(forms.Form):
    def __init__(self, num_required, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(9):
            required = (i < num_required) or i == 0
            attrs = {'class': 'form-control',
                     'data-multitext-target': 'text'}
            if(not required):
                attrs['hidden'] = None
            f = forms.CharField(label='',
                                required=required,
                                widget=forms.TextInput(attrs=attrs))
            self.fields['text_{}'.format(i)] = f

class TextListQuestion(Question):
    minimum_required = models.IntegerField(null=True, blank=True)
    allow_more = models.BooleanField(default=False)

    def form(self, *args, **kwargs):
        return TextListingForm(self.minimum_required, *args, **kwargs)

    def for_dict(self, data):
        ret = []
        for key in data.keys():
            ret.append(data[key])
        return ret

class ContactForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

class ContactQuestion(Question):
    def form(self, *args, **kwargs):
        return ContactForm(*args, **kwargs)
    def for_dict(self, data):
        return data

class IntegerForm(forms.Form):
    number = forms.IntegerField(label="", required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))

class IntegerQuestion(Question):
    def form(self, *args, **kwargs):
        return IntegerForm(*args, **kwargs)
    def for_dict(self, data):
        return data['number']

class CustomQuestion(Question):
    custom_form = models.CharField(blank=True, null=True, max_length=50)

    def form(self, *args, **kwargs):
        pass
    def for_dict(self, data):
        return data
