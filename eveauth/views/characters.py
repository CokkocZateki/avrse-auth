from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from eveauth.models import Character, Asset

@login_required
def characters_index(request):
    context = {
        "characters": request.user.characters.all().annotate(
            total_sp=Sum('skills__skillpoints_in_skill')
        ).order_by('-total_sp'),
    }

    return render(request, "eveauth/characters.html", context)


@login_required
def characters_delete(request, id):
    character = Character.objects.get(id=id)
    if character.owner == request.user:
        token = character.token

        # Wipe character
        character.owner = None
        character.token = None
        character.save()

        # Delete social auth
        token.delete()

        # Return to characters page with success message
        messages.success(request, "Disconnected auth token for %s" % character.name)
    else:
        messages.warning(request, "You don't own %s" % character.name)

    return redirect("characters_index")


@login_required
def assets_index(request):
    user = request.user

    context = {
        "view_ship": "assets_viewship",
        "user": user,
        "assets": Asset.objects.filter(
                character__owner=user,
                type__group__category__id=6,
                singleton=True,
                system__isnull=False
            ).exclude(
                type__group__id__in=[
                    29,             # Capsule
                    237,            # Noobship
                ]
            ).prefetch_related(
                'system',
                'system__region',
                'character',
                'type',
                'type__group'
            ).order_by(
                'system__region__name',
                'system__name',
                'character__name',
                '-type__mass',
                'type__group__name',
                'type__name'
            ).all()
    }

    return render(request, "eveauth/view_ships.html", context)


@login_required
def assets_viewship(request, id):
    ship = Asset.objects.get(id=id)

    if ship.character.owner == request.user:
        context = {
            "ship": ship,
            "view_ship": "assets_viewship"
        }
        return render(request, "eveauth/view_ship.html", context)
