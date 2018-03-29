from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Case, When
from .models import Idea, Criterion,Popular_Vote, Phase, Phase_History,Category, Comment, UserProfile
from .forms import IdeaForm, CriterionForm,IdeaFormUpdate, CategoryForm
from .singleton import Profanity_Check
from django import forms
from wordfilter import Wordfilter
import os
import json

def index(request):
    if request.user.is_authenticated:
        return idea_list(request)
    return render(request, 'ideax/index.html')

@login_required
def idea_list(request):

    try:
        print("Checando...")
        user_profile = UserProfile.objects.get(user=request.user)
        print(user_profile)

    except UserProfile.DoesNotExist:
        print("Caiu na exceção")
        user_profile = UserProfile()
        user_profile.user = request.user
        user_profile.save()
        print("criou um userprofile")
        print(user_profile)

    ideas = get_ideas_init(request)
    ideas['phases'] = Phase.choices()
    return render(request, 'ideax/idea_list.html', ideas)

@login_required
def get_ideas_init(request):
    ideas_dic = dict()
    ideas_dic['ideas'] = Idea.objects.filter(discarded=False).annotate(count_like=Count(Case(When(popular_vote__like = True, then=1)))).order_by('-count_like')
    ideas_dic['ideas_liked'] = get_ideas_voted(request, True)
    ideas_dic['ideas_disliked'] = get_ideas_voted(request, False)
    ideas_dic['ideas_created_by_me'] = get_ideas_created(request)
    ideas_dic['link_title'] = True
    return ideas_dic


def get_phases():
    phase_dic = dict()
    phase_dic['phases'] = Phase.choices()
    return phase_dic

@login_required
def idea_detail(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    context={'idea': idea, 'link_title': False}
    data = dict()
    data['html_form'] = render_to_string('ideax/includes/idea_detail.html', context, request=request,)
    return JsonResponse(data)

def idea_filter(request, phase_pk):
    if phase_pk == 0:
        filtered_phases = Phase_History.objects.filter(current=1)
    else:
        filtered_phases = Phase_History.objects.filter(current_phase=phase_pk, current=1)
    #filtered_phases = sorted(filtered_phases, key=operator.attrgetter('idea.creation_date'))
    ideas = [];
    for phase in filtered_phases:
        if phase.idea.discarded == False:
            ideas.append(phase.idea)
    ideas.sort(key=lambda idea:idea.creation_date)
    context={'ideas': ideas, 'link_title': True}
    data = dict()
    data['html_idea_list'] = render_to_string('ideax/idea_list_loop.html', context, request=request)
    #return render(request, 'ideax/idea_list.html', ideas)
    if not ideas:
        data['html_idea_list'] = render_to_string('ideax/includes/empty.html', request=request)
    return JsonResponse(data)


@login_required
def save_idea(request, form, template_name, new=False):
    data = dict()
    if request.method == "POST":
        if form.is_valid():
            idea = form.save(commit=False)

            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                user_profile = UserProfile(user=request.user)
                user_profile.save()

            idea.author = user_profile

            if new:
                idea.creation_date = timezone.now()
                idea.phase= Phase.GROW.id
                idea.save()
                phase_history = Phase_History(current_phase=Phase.GROW.id,previous_phase=0, date_change=timezone.now(), idea=idea, author=user_profile, current=True)
                phase_history.save()
            else:
                idea.save()
            #data['form_is_valid'] = True
            #ideas = get_ideas_init(request)
            #data['html_list'] = render_to_string('ideax/idea_list_loop.html', ideas)
            return redirect('idea_list')
        #else:
            #data['form_is_valid'] = False
            #form = IdeaForm()

    #context = {'form' : form}
    #data['html_form'] = render_to_string(template_name, context, request=request,)

    return render(request, template_name, {'form': form})
    #return JsonResponse(data)

@login_required
def idea_new(request):
    if request.method == "POST":
        form = IdeaForm(request.POST)
        #form = IdeaForm({'title':request.POST.get('title', None),
        #                'oportunity':request.POST.get('oportunity', None),
        #                'solution':request.POST.get('solution', None),
        #                'target':request.POST.get('target', None),
        #                'category':request.POST.get('category', None)}
        #                )
    else:
        form = IdeaForm()

    return save_idea(request, form, 'ideax/idea_new.html', True)
"""
    if request.is_ajax():
        return save_idea(request, form, 'ideax/idea_new.html', True)
    else:
        return redirect('idea_list')
"""
@login_required
def idea_edit(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if request.method == "POST":
        form = IdeaForm(request.POST, instance=idea)
    else:
        form = IdeaForm(instance=idea)

    return save_idea(request, form, 'ideax/idea_edit.html')


@login_required
def idea_remove(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    data = dict()
    if request.method == 'POST':
        idea.discarded = True
        idea.save()
        data['form_is_valid'] = True
        ideas = get_ideas_init(request)
        data['html_list'] = render_to_string('ideax/idea_list_loop.html', ideas)
    else:
        context = {'idea' : idea}
        data['html_form'] = render_to_string('ideax/includes/partial_idea_remove.html', context, request=request,)

    return JsonResponse(data)

@login_required
def criterion_new(request):
    if request.method == "POST":
        form = CriterionForm(request.POST)
        if form.is_valid():
            criterion = form.save(commit=False)
            criterion.save()
            return redirect('criterion_list')
    else:
        form = CriterionForm()

    return render(request, 'ideax/criterion_edit.html', {'form': form})

@login_required
def criterion_list(request):
    criterion = Criterion.objects.all()
    return render(request, 'ideax/criterion_list.html', {'criterions': criterion})

@login_required
def criterion_edit(request, pk):
    criterion = get_object_or_404(Criterion, pk=pk)
    if request.method == "POST":
        form = CriterionForm(request.POST, instance=criterion)
        if form.is_valid():
            criterion = form.save(commit=False)
            criterion.save()
            return redirect('criterion_list')
    else:
        form = CriterionForm(instance=criterion)
    return render(request, 'ideax/criterion_edit.html', {'form': form})

@login_required
def criterion_remove(request, pk):
    criterion = get_object_or_404(Criterion, pk=pk)
    criterion.delete()
    return redirect('criterion_list')

def open_category_new(request, ):
    data = dict()
    context = {'form': CategoryForm()}
    data['html_form'] = render_to_string('ideax/category_new.html', context,request=request,)
    return JsonResponse(data)

def category_new(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
    else:
        form = CategoryForm()

    if request.is_ajax():
        return save_category(request, 'ideax/category_new.html', form)
    else:
        return redirect('category_list')

def save_category(request, template_name, form):
    data = dict()
    if request.method == "POST":
        if form.is_valid():
            category = form.save(commit=False)
            category.save()
            data['form_is_valid'] = True
        else:
            data['form_is_valid'] = False

        data['html_list'] = render_to_string('ideax/includes/partial_category_list.html', get_category_list())
    context = {'form' : form}
    data['html_form'] = render_to_string(template_name, context, request=request,)

    return JsonResponse(data)


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
    else:
        form = CategoryForm(instance=category)

    return save_category(request,'ideax/category_edit.html',form)
def category_remove(request, pk):
    category = get_object_or_404(Category, pk=pk)
    data = dict()
    if request.method == 'POST':
        category.discarded = True
        category.save()
        data['form_is_valid'] = True
        data['html_list'] = render_to_string('ideax/includes/partial_category_list.html', get_category_list())
    else:
        context = {'category': category}
        data['html_form'] = render_to_string('ideax/includes/partial_category_remove.html', context, request=request)

    return JsonResponse(data)

def category_list(request):
    return render(request, 'ideax/category_list.html', get_category_list())


def get_category_list():
    return {'category_list': Category.objects.filter(discarded=False)}

@login_required
def like_popular_vote(request, pk):
    vote = Popular_Vote.objects.filter(voter=request.user,idea__pk=pk)

    idea_ = Idea.objects.get(pk=pk)
    like_boolean =  request.path.split("/")[3] == "like"

    if vote.count() == 0:
        like = Popular_Vote(like=like_boolean,voter=request.user,voting_date=timezone.now(),idea=idea_)
        like.save()
    else:
        if vote[0].like == like_boolean:
            vote.delete()
            like_boolean = None
        else:
            vote.update(like=like_boolean)


    data = dict()
    data['qtde_votes_likes'] = idea_.count_likes()
    data['qtde_votes_dislikes'] = idea_.count_dislikes()
    data['class'] = like_boolean

    return JsonResponse(data)

@login_required
def get_ideas_voted(request, vote):
    ideas_voted = []
    if request.user.is_authenticated:
        ideas_voted = Popular_Vote.objects.filter(like=vote, voter=UserProfile(user=request.user)).values_list('idea_id',flat=True)

    return ideas_voted

@login_required
def get_ideas_created(request):
    ideas_created = []
    if request.user.is_authenticated:
        ideas_created = Idea.objects.filter(author=UserProfile(user=request.user)).values_list('id',flat=True)

    return ideas_created

def change_idea_phase(request, pk, new_phase):
    idea = Idea.objects.get(pk=pk)
    phase = Phase.get_phase_by_id(new_phase)

    if phase != None:
        phase_history_current = Phase_History.objects.get(idea=idea, current=True)
        phase_history_current.current = False
        phase_history_current.save()

        phase_history_new = Phase_History(current_phase=phase.id,previous_phase=phase_history_current.current_phase, date_change=timezone.now(), idea=idea, author=request.user, current=True)
        phase_history_new.save()

    return redirect('index')

def form_redirect(request, pk):
    idea = Idea.objects.get(id=pk)
    comments = idea.comment_set.all()
    #Comment.objects.filter(idea=idea)

    return render(request, 'ideax/idea_detail.html', {"comments": comments, "idea" : idea, "idea_id" : idea.pk})


def post_comment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'msg': "You need to log in to post new comments."}, status=500)

    raw_comment = request.POST.get('commentContent', None)
    parent_id = request.POST.get('parentId', None)
    author = request.user
    idea_id = request.POST.get('ideiaId', None)

    if Profanity_Check.wordcheck().blacklisted(raw_comment):
        return JsonResponse({'msg': "Please check your message it has inappropriate content."}, status=500)

    if not raw_comment:
        return JsonResponse({'msg': "You have to write a comment."},status=500)

    if not parent_id:
        parent_object = None
    else:
        parent_object = Comment.objects.get(id=parent_id)

    idea = Idea.objects.get(id=idea_id)

    comment = Comment(author=author,
                      raw_comment=raw_comment,
                      parent=parent_object,
                      idea=idea,
                      date=timezone.now(),
                      comment_phase=1)

    comment.save()

    return JsonResponse({"msg" : "Your comment has been posted."})

def idea_comments(request, pk):
    data = dict()
    data['html_list'] = render_to_string('ideax/includes/partial_comments.html',
                                         {"comments" : Comment.objects.filter(idea__id=pk), "idea_id" : pk})

    return JsonResponse(data)
