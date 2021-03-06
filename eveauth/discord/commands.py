from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from terminaltables import AsciiTable

from avrseauth.settings import members, blues
from eveauth.models import Character
from sde.models import System, Region

ranges = {
    30: 6,      # Titans
    659: 6,     # Supers
    485: 7,     # Dreads
    547: 7,     # Carriers
    1538: 7,    # FAXes
    898: 8,     # Black Ops
}

supers = [
    30,
    659
]


class BotCommands:
    def __init__(self, tokens, user, event):
        self.tokens = tokens
        self.user = user
        self.event = event


    def monowrap(self, text):
        return "```%s```" % text

    def get_personal_chars(self):
        self.search = " ".join(self.tokens[1:])
        return self.user.characters.filter(name__istartswith=self.search)

    def get_all_chars(self):
        self.search = " ".join(self.tokens[1:])
        return Character.objects.filter(
            owner__isnull=False,
            name__istartswith=self.search
        )

    def get_user(self):
        self.search = " ".join(self.tokens[1:])
        return User.objects.filter(
            characters__name__istartswith=self.search
        ).first()

    def get_system(self):
        self.search = " ".join(self.tokens[1:])
        return System.objects.filter(
            name__istartswith=self.search
        )

    def get_region(self):
        self.search = " ".join(self.tokens[1:])
        return Region.objects.filter(
            name__istartswith=self.search
        )

    def reply_chunked(self, reply):
        if len(self.monowrap(reply)) < 2000:
            self.event.reply(self.monowrap(reply))
        else:
            lines = reply.split("\n")
            out = ""
            while len(lines) > 0:
                cur = lines.pop(0)
                test = "%s\n%s" % (
                    out,
                    cur
                )
                if len(self.monowrap(test)) < 1998:
                    out = test
                else:
                    self.event.reply(self.monowrap(out))
                    out = cur
            self.event.reply(self.monowrap(out))


    def supers(self):
        chars = Character.objects.filter(
            owner__isnull=False,
            ship__group_id__in=supers
        ).order_by(
            'ship__group__name',
            'ship__name',
            'system__region__name',
            'system__name',
            'owner__username',
            'name'
        )

        if chars.count() > 1:
            table = [["Owner", "Char", "Ship", "System", "Region", "Fatigue"]]
            for char in chars.all():
                table.append(
                    [
                        char.owner.profile.character.name,
                        char.name,
                        char.ship.name,
                        char.system.name,
                        char.system.region.name,
                        char.fatigue_text()
                    ]
                )

            self.reply_chunked(
                "All Supers\n%s" % (
                    AsciiTable(table).table
                )
            )


    def whoin(self):
        # Check for location
        system = self.get_system()
        region = self.get_region()

        chars = None
        if system.count() == 1:
            location = system.first()
            chars = Character.objects.filter(
                system=location
            )
        elif region.count() == 1:
            location = region.first()
            chars = Character.objects.filter(
                system__region=location
            )

        if chars != None:
            table = [["Owner", "Char", "Ship", "System", "Fatigue"]]

            for char in chars.order_by(
                'system__name',
                'ship__group__name',
                'ship__name',
                'name'
            ).all():
                table.append(
                    [
                        char.owner.profile.character.name,
                        char.name,
                        char.ship.name,
                        char.system.name,
                        char.fatigue_text()
                    ]
                )

            self.reply_chunked(
                "Characters in %s\n%s" % (
                    location.name,
                    AsciiTable(table).table
                )
            )


    def whoinrange(self):
        target = self.get_system()
        if target != None:
            target = target.first()
            chars = Character.objects.filter(owner__isnull=False)
            table = [["Owner", "Char", "Ship", "System", "Range", "Fatigue"]]

            for char in chars.prefetch_related(
                'system',
                'ship'
            ).order_by(
                'ship__group__name',
                'ship__name',
                'name'
            ).all():
                if char.ship.group_id in ranges.keys():
                    if target.distance(char.system, True) <= ranges[char.ship.group_id]:
                        table.append(
                            [
                                char.owner.profile.character.name,
                                char.name,
                                char.ship.name,
                                char.system.name,
                                "%s ly" % round(char.system.distance(target, ly=True), 2),
                                char.fatigue_text()
                            ]
                        )

            self.reply_chunked(
                "Characters in range of %s\n%s" % (
                    target.name,
                    AsciiTable(table).table
                )
            )


    def alts(self):
        user = self.get_user()
        self.event.reply(
            self.monowrap(
                "Alts of %s\n%s" % (
                    user.profile.character.name,
                    ", ".join(
                        user.characters.all().values_list('name', flat=True)
                    )
                )
            )
        )


    def fatigue(self, admin=False):
        if admin:
            chars = self.get_all_chars()
        else:
            chars = self.get_personal_chars()

        if self.search == "":
            self.event.reply(
                self.monowrap(
                    "!fatigue <partial character name>"
                )
            )

        elif chars.count() == 0:
            self.event.reply("No Characters Found")

        elif chars.count() > 1:
            self.event.reply(
                self.monowrap(
                    "Multiple Chars Found:\n%s" % (
                        ", ".join(
                            map(lambda x: x.name,
                                chars.filter(
                                    Q(corp__id__in=members['corps'])
                                    | Q(alliance__id__in=members['alliances'])
                                    | Q(corp__id__in=blues['corps'])
                                    | Q(alliance__id__in=blues['alliances'])
                                ).all()
                            )
                        )
                    )
                )
            )

        else:
            char = chars.first()
            self.event.reply(
                "**%s**: %s" % (
                    char.name,
                    char.fatigue_text()
                )
            )
