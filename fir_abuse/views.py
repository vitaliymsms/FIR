from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import Template
from django.conf import settings
from json import dumps

from incidents.views import is_incident_handler
from incidents.models import Incident, BusinessLine
from fir_artifacts.models import Artifact 

from fir_abuse.models import Abuse, EmailForm

from fir.whois import Whois


@login_required
@user_passes_test(is_incident_handler)
def emailform(request):
    email_form = EmailForm()

    return render(request, 'fir_abuse/emailform.html', {'form': email_form})


@login_required
@user_passes_test(is_incident_handler)
def send_email(request):
    if request.method == 'POST':
        try:
            from django.core.mail import EmailMultiAlternatives
            behalf = request.POST['behalf']
            to = request.POST['to']
            cc = request.POST['cc']
            bcc = request.POST['bcc']

            subject = request.POST['subject']
            body = request.POST['body']

            if hasattr(settings, 'REPLY_TO'):
                reply_to = {'Reply-To': settings.REPLY_TO, 'Return-Path': settings.REPLY_TO}
            else:
                reply_to = {}

            e = EmailMultiAlternatives(
                subject=subject,
                from_email=behalf,
                to=to.split(';'),
                cc=cc.split(';'),
                bcc=bcc.split(';'),
                headers=reply_to
            )
            e.attach_alternative(body, 'text/html')
            e.content_subtype = 'html'
            e.send()

            return HttpResponse(dumps({'status': 'ok'}), content_type="application/json")

        except Exception, e:
            return HttpResponse(dumps({'status': 'ko', 'error': str(e)}), content_type="application/json")

    return HttpResponseBadRequest(dumps({'status': 'ko'}), content_type="application/json")


@login_required
@user_passes_test(is_incident_handler)
@receiver(post_save, sender=Artifact)
def analyze_artifacts(sender, instance=None, created=False, **kwargs):
    """TODO: Docstring for analyze_artifacts.

    :arg1: TODO
    :returns: TODO

    """
    tasks = {
            'hostname': Whois.analyze.delay,
            'email': Whois.analyze.delay
            }

    if created:
        if instance.type in tasks:
            result = tasks[instance.type]({'type':instance.type, 'value':instance.value})
    import ipdb; ipdb.set_trace()
