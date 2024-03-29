from django.shortcuts import render,redirect
from django.http import HttpResponse
from Movies.models import Movie,MovieLab,MovieComment
from Comments.models import Comments
from Filmmakers.models import Celebrity
import os
import json
#from django.core.serializers.json import json


def return_home_movies(request):
    #按照上映时间抽取最新条目
    movie_objects = Movie.objects.all().order_by('-movie_releaseTime')[:2]
    id_num = 1
    movies = []
    for movie in movie_objects:
        print(movie.movie_name)
        movies.append({
            "id": id_num,
            "title": movie.movie_name,
            "img": "/image/" + str(movie.movie_cover),
            "url": "/movie/" + str(movie.movie_id)
        })
        id_num += 1

    result = {
        "success": True,
        "data": {
            "movies": movies
        }
    }
    
    return HttpResponse(json.dumps(result,ensure_ascii=False), content_type="application/json", charset='utf-8')

def return_movie_json(request, movie_id):
    movie = Movie.objects.get(movie_id=movie_id)
    comment_objects = MovieComment.objects.filter(movie=movie)
    comment_list = []
    if comment_objects:
        for comment in comment_objects:
            # comment_list.append({"user": comment.user.user_name,"content":comment.content})
            comment_list.append({"user": comment.author_name, "content": comment.content})

    lab_objects = movie.lab.all()  # return all labs objects for this movie
    lab_list = []
    if lab_objects:
        for lab in lab_objects:
            lab_list.append({"type": lab.lab_content, "url": "#"})

    type_objects = movie.types.all()  # return all type objects for this movie
    types = ''
    if type_objects:
        for movie_type in type_objects:
            types = types + movie_type.type_name + ','
        types = types[:-1]

    director_objects = Celebrity.objects.filter(movie=movie, roletable__role='director')
    directors = ''
    for director in director_objects:
        directors = directors + director.celebrity_name + ' / '
    directors = directors[:-3]

    actor_objects = Celebrity.objects.filter(movie=movie, roletable__role='actor')
    actors = ''
    actor_imgs = []
    if actor_objects:
        for actor in actor_objects:
            actors = actors + actor.celebrity_name + ' '
            # actor_imgs.append({"img": "/image/"+str(actor.celebrity_cover)})
            actor_imgs.append({"img": actor.celebrity_cover})
        actors = actors[:-1]

    result = {
        # "id": movie_id,
        "title": movie.movie_name,
        "name": movie.movie_name,
        # "poster": "/image/" + str(movie.movie_cover),
        "poster": movie.movie_cover,
        "showtime": movie.movie_releaseTime,  # movie.movie_releaseTime.strftime('%Y-%m-%d')
        "showpos": movie.movie_showPos,
        "length": movie.movie_length,
        "type": types,
        "director": directors,
        "actor": actors,
        "score": movie.movie_grades,
        "introduction": movie.movie_intro,
        "actorimg": actor_imgs,
        "lab": lab_list,
        "comment": comment_list,

    }
    return HttpResponse(json.dumps(result,ensure_ascii=False), content_type="application/json", charset='utf-8')


def get_movies(request):
    type = request.GET.get('type')  # 获取请求的类别值
    print(type)

    result = {
        "data": [
            {
                "title": "玩具总动员",
                "score": "8.4",
                "date": "1995",
                "type": "喜剧,动画,家庭",
                # "img": "/image/MovieCover/20200131/p2557573348.webp",
                "img": "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p2220722175.jpg",
                "url": "../detail/1"
            }
        ]
    }
    return HttpResponse(json.dumps(result,ensure_ascii=False), content_type="application/json", charset='utf-8')
