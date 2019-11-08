"""Aegis Models"""
import logging
import os

from django.db import models
from django.core.exceptions import ValidationError

LOG_LEVELS = [
    (str(l), n) for l, n in logging._levelNames.iteritems() if isinstance(
            l, int) ]


class Category(models.Model):
    name = models.CharField(
            max_length=100,
            unique=True,
            verbose_name=u'Alert/Report category')
    description = models.TextField(
            blank=True,
            null=True,
            verbose_name=u'Description')
            
    class Meta:
        db_table = u'category'
        verbose_name = u'Category of alerts/reports'
        verbose_name_plural = u'Categories of alerts/reports'
        
    def __unicode__(self):
        return self.name

    def get_all_jobs(self, op_id=None):
        jobs = Job.objects.filter(category__id=self.id)
        if op_id:
            jobs = jobs.filter(operator__id=op_id)
    	return jobs
    
class MailID(models.Model):
    email_id = models.EmailField(
            unique=True,
            verbose_name=u'Email ID')
    name = models.CharField(
            max_length=100,
            blank=True,
            null=True,
            verbose_name=u'Name')
    
    class Meta:
        db_table = u'mailid'
        verbose_name = u'Email ID'
        verbose_name_plural = u'Email IDs'
        
    def __unicode__(self):
        return '%s <%s>' % (
            self.name,
            self.email_id
            )

class Operator(models.Model):
    name = models.CharField(
            max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    
    class Meta:
        db_table = u'operator'
        verbose_name = u'Operator'
        verbose_name_plural = u'Operator'


    def __unicode__(self):
        return self.name
    
class Job(models.Model):
    name = models.CharField(
            max_length=200,
            verbose_name=u'Name of job')
    operator = models.ForeignKey(Operator)
    category = models.ForeignKey(
            Category,
            verbose_name=u'Category')
    is_running = models.BooleanField(
            default=False,
            verbose_name=u'Is running?')
    is_scheduled = models.BooleanField(
            default=False,
            verbose_name=u'Schedule/Unschedule',
            help_text='checked means scheduled')
    last_execution = models.DateTimeField(
            null=True,
            blank=True,
            verbose_name=u'Time of last execution')
    description = models.TextField(
            blank=True,
            null=True,
            verbose_name=u'Job description'
            )
    to_mail_ids = models.ManyToManyField(
            MailID,
            related_name='to+',
            verbose_name=u'To mail ids')
    cc_mail_ids = models.ManyToManyField(
            MailID,
            null=True, 
            blank=True,
            related_name='cc+',
            verbose_name=u'Cc mail ids')
    bcc_mail_ids = models.ManyToManyField(
            MailID,
            null=True, blank=True,
            related_name='bcc+',
            verbose_name=u'Bcc mail ids')
    from_id = models.EmailField(
            blank=True,
            null=True,
            verbose_name=u'ID from alert mails to be send')
    mail_head = models.CharField(
            max_length=200,
            null=True,
            blank=True,
            verbose_name=u'Subject of mail alert')
    mail_html_body = models.TextField(
            null=True,
            blank=True,
            verbose_name=u'Mail html body'
            )
    sch_hour = models.CharField(
            max_length=30,
            default='*',
            verbose_name=u'Hours(crontab based format)')
    sch_minute = models.CharField(
            max_length=30,
            default='*',
            verbose_name=u'Minutes(crontab based format)')
    sch_frequency = models.CharField(
            max_length=30,
            default='*',
            verbose_name=u'Days in a week(crontab based format)'
            )
    is_python_script = models.BooleanField(
            default=True,
            verbose_name=u'Is a python script?'
            )
    script_location = models.CharField(
            max_length=100,
            blank=True,
            null=True,
            verbose_name=u'Location of the script(in case of python)'
            )
        
    def __unicode__(self):
        return self.name
    
    def clean(self):
        if self.is_python_script and (not os.path.exists(self.script_location)):
            raise ValidationError(
                'Script you provided, doesn"t exist.')
    
    class Meta:
        db_table = u'sch_job'
        verbose_name = u'Scheduled Job'
        verbose_name_plural = u'Scheduled Jobs'
        unique_together = (('name', 'operator'),)

class JobConf(models.Model):
    job = models.ForeignKey(
            Job,
            verbose_name=u'Which Job')
    field_name = models.CharField(
            max_length=30,
            verbose_name=u'Field')
    field_type = models.CharField(
            max_length=1,
            choices=(('I', 'int'), ('S', 'str'), ('F', 'float')))
    value = models.CharField(
            max_length=100,
            blank=True,
            null=True)
    custom_value = models.TextField(
            blank=True,
            null=True)

    def __unicode__(self):
        return '%s:%s' % (self.field_name, self.value)
    
    class Meta:
        db_table = u'job_config'
        unique_together = (('job', 'field_name'),)
        verbose_name = u'Script Parameters'
        verbose_name_plural = u'Script Parameters'
    
    def clean(self):
        field_type_dict = {'I': int, 'S': str, 'F': float}
        if self.value:
            data_type = field_type_dict.get(self.field_type)
            try:
                value = data_type(self.value)
            except:
                raise ValidationError(
                'Value you entered is not matching with field type')
            
        if not(self.value or self.custom_value):
            raise ValidationError(
                'At least one value be required.') 


class JobResultField(models.Model):
    job = models.ForeignKey(
            Job,
            verbose_name=u'Which Job')
    field_name = models.CharField(
            max_length=30,
            verbose_name=u'Field')
    field_type = models.CharField(
            max_length=1,
            choices=(('I', 'int'), ('S', 'str'), ('F', 'float')))
            
    class Meta:
        db_table = u'job_result_field'
        unique_together = (('job', 'field_name'),)
        verbose_name = u'Result fields of job'
        verbose_name_plural = u'Result fields of a job'
        


class RunningStatus(models.Model):
    job = models.ForeignKey(
            Job,
            verbose_name=u'Job')
    status = models.CharField(
            max_length=1,
            default='E',
            choices = (
                ('E', 'On Execution'),
                ('F', 'Failed'),
                ('S', 'Success')
                ),
            verbose_name=u'Present Status')
    start_time = models.DateTimeField(
            verbose_name=u'Execution starting time'
            )
    end_time = models.DateTimeField(
            null=True,
            blank=True,
            verbose_name=u'Execution ending time')
            
    def __unicode__(self):
        return '<%s> %s %s' % (
            self.job.name,
            self.start_time,
            self.get_status_display())
    
    class Meta:
        db_table = u'running_status'
        verbose_name = u'Running Status of job'
        verbose_name_plural = u'Running Status of jobs'
        ordering = ('-start_time', )
        
class LogStatus(models.Model):
    runningjob = models.ForeignKey(
            RunningStatus,
            verbose_name=u'Which running instance')
    level = models.CharField(
            max_length=2,
            verbose_name=u'Level of log',
            choices=LOG_LEVELS)
    message = models.TextField(
            verbose_name=u'Message'
            )
    log_time = models.DateTimeField(
            auto_now=True,
            verbose_name=u'Logged time'
            )
    
    class Meta:
        db_table = u'job_log_status'
        verbose_name = u'Job log status'
        verbose_name_plural = u'Job log statuses'
        ordering = ('-log_time', )
        
    def __unicode__(self):
        return self.message
    

class JobResultValue(models.Model):
    runningjob = models.ForeignKey(
            RunningStatus,
            verbose_name=u'Which running instance')
    name = models.CharField(
            max_length=100,
            verbose_name=u'Name')
    value = models.CharField(
            max_length=100,
            verbose_name=u'Value')
    
    class Meta:
        db_table = u'job_result_value'
        unique_together = (('runningjob', 'name', 'value'),)
        verbose_name = u'Values of job'
        verbose_name_plural = u'Values of jobs'

class SMTP(models.Model):
    server = models.CharField(
            unique=True,
            max_length=100,
            verbose_name=u'SMTP server')
    port = models.CharField(
            max_length=5,
            verbose_name=u'Port')
            
    class Meta:
        db_table = u'smtp'
        verbose_name = 'SMTP connection details'
        verbose_name_plural = 'SMTP connection details'
