"""
All tests for the proctored_exams.py
"""
import json
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch
from edx_proctoring.models import ProctoredExam
from edx_proctoring.views import require_staff

from .utils import (
    LoggedInTestCase
)
from mock import Mock

from edx_proctoring.urls import urlpatterns


class ProctoredExamsApiTests(LoggedInTestCase):
    """
    All tests for the views.py
    """

    def setUp(self):
        """
        Build out test harnessing
        """
        super(ProctoredExamsApiTests, self).setUp()

    def test_no_anonymous_access(self):
        """
        Make sure we cannot access any API methods without being logged in
        """
        self.client = Client()  # use AnonymousUser on the API calls
        for urlpattern in urlpatterns:
            if hasattr(urlpattern, 'name'):
                try:
                    response = self.client.get(reverse(urlpattern.name))
                except NoReverseMatch:
                    # some of our URL mappings may require a argument substitution
                    try:
                        response = self.client.get(reverse(urlpattern.name, args=[0]))
                    except NoReverseMatch:
                        # some require 2 args.
                        response = self.client.get(reverse(urlpattern.name, args=["0/0/0", 0]))

                self.assertEqual(response.status_code, 403)


class StudentProctoredExamAttempt(LoggedInTestCase):
    """
    Tests for StudentProctoredExamAttempt
    """
    def setUp(self):
        super(StudentProctoredExamAttempt, self).setUp()
        self.user.is_staff = True
        self.user.save()
        self.client.login_user(self.user)

    def test_get_exam_attempt(self):
        """
        Test Case for retrieving student proctored exam attempt status.
        """
        response = self.client.get(
            reverse('edx_proctoring.proctored_exam.attempt')
        )
        self.assertEqual(response.status_code, 200)


class ProctoredExamViewTests(LoggedInTestCase):
    """
    Tests for the ProctoredExamView
    """
    def setUp(self):
        super(ProctoredExamViewTests, self).setUp()
        self.user.is_staff = True
        self.user.save()
        self.client.login_user(self.user)

    def test_create_exam(self):
        """
        Test the POST method of the exam endpoint to create an exam.
        """
        exam_data = {
            'course_id': "a/b/c",
            'exam_name': "midterm1",
            'content_id': '123aXqe0',
            'time_limit_mins': 90,
            'external_id': '123',
            'is_proctored': True,
            'is_active': True
        }
        response = self.client.post(
            reverse('edx_proctoring.proctored_exam.exam'),
            exam_data
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertGreater(response_data['exam_id'], 0)

        # Now lookup the exam by giving the exam_id returned and match the data.
        response = self.client.get(
            reverse('edx_proctoring.proctored_exam.exam_by_id', kwargs={'exam_id': response_data['exam_id']})
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['course_id'], exam_data['course_id'])
        self.assertEqual(response_data['exam_name'], exam_data['exam_name'])
        self.assertEqual(response_data['content_id'], exam_data['content_id'])
        self.assertEqual(response_data['external_id'], exam_data['external_id'])
        self.assertEqual(response_data['time_limit_mins'], exam_data['time_limit_mins'])

    def test_get_exam_by_id(self):
        """
        Tests the Get Exam by id endpoint
        """
        # Create an exam.
        proctored_exam = ProctoredExam.objects.create(
            course_id='test_course',
            content_id='test_content',
            exam_name='Test Exam',
            external_id='123aXqe3',
            time_limit_mins=90
        )

        response = self.client.get(
            reverse('edx_proctoring.proctored_exam.exam_by_id', kwargs={'exam_id': proctored_exam.id})
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['course_id'], proctored_exam.course_id)
        self.assertEqual(response_data['exam_name'], proctored_exam.exam_name)
        self.assertEqual(response_data['content_id'], proctored_exam.content_id)
        self.assertEqual(response_data['external_id'], proctored_exam.external_id)
        self.assertEqual(response_data['time_limit_mins'], proctored_exam.time_limit_mins)

    def test_decorator_staff_user(self):
        """
        Test assert require_staff before hitting any api url.
        """
        func = Mock()
        decorated_func = require_staff(func)
        request = self.mock_request()
        response = decorated_func(request)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(func.called)

    def mock_request(self):
        """
        mock request
        """
        request = Mock()
        self.user.is_staff = False
        self.user.save()
        request.user = self.user
        return request
