

"""Recommendationsystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import index
##from . import UserDashboard
##from . import index
from django.conf import settings
from django.conf.urls.static import static
from .index import feedback_page, chatbot_query
from django.contrib.auth import views as auth_views


urlpatterns = [


    path('signup', index.signup),
    path('signin', index.signin),
    
    path('', index.index),
    path('up', index.up),
    path('login/up', index.up),
    path('index', index.index),
    path('login/index', index.index),
    path('about', index.about),
    path('login/about', index.about),
    path('team', index.team),
    path('login/team', index.team),
    path('feedback/', index.feedback_page, name='feedback_page'),  # Dedicated feedback page
    path('feedback/', index.feedback_view, name='feedback'),
    path('submit_feedback/<int:feedback_id>/', index.submit_feedback, name='submit_feedback'),
    path('chat', index.chat_view, name='chat'),  # Chat page
    path('Reg', index.Reg),
    path('registration', index.registration),
    path('login/registration', index.registration),
    path('dologin', index.dologin),
    path('login/dologin', index.dologin),
    path('login/', index.login),
    path('login/login', index.login),
    path('Dashboard', index.Dashboard),
    path('login/Dashboard', index.Dashboard),
    path("chatbot-query/", chatbot_query, name="chatbot_query"),
    path('View', index.View),
    path('up/', index.up, name='upload_pdf'),
    path('progress/', index.check_progress, name='check_progress'),  # Progress API
    #path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),



    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



