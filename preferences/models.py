from django.db import models
from django.dispatch import receiver

import preferences
from preferences.managers import SingletonManager
from django.utils.translation import ugettext_lazy as _


class Preferences(models.Model):
    objects = models.Manager()
    singleton = SingletonManager()
    sites = models.ManyToManyField('sites.Site', null=True, blank=True)

    def __unicode__(self):
        """
        Include site names.
        """
        site_names = [site.name for site in self.sites.all()]
        prefix = self._meta.verbose_name_plural.capitalize()

        if len(site_names) > 1:
            return _('{0} for sites {1} and {2}.').format(prefix, ', '.\
                    join(site_names[:-1]), site_names[-1])
        elif len(site_names) == 1:
            return _('{0} for site {1}.').format(prefix, site_names[0])
        return _('{0} without assigned site.').format(prefix)


@receiver(models.signals.class_prepared)
def preferences_class_prepared(sender, *args, **kwargs):
    """
    Adds various preferences members to preferences.preferences,
    thus enabling easy access from code.
    """
    cls = sender
    if issubclass(cls, Preferences):
        # Add singleton manager to subclasses.
        cls.add_to_class('singleton', SingletonManager())
        # Add property for preferences object to preferences.preferences.
        setattr(preferences.Preferences, cls._meta.object_name, \
                property(lambda x: cls.singleton.get()))


@receiver(models.signals.m2m_changed)
def site_cleanup(sender, action, instance, **kwargs):
    """
    Make sure there is only a single preferences object per site.
    So remove sites from pre-existing preferences objects.
    """
    if action == 'post_add':
        if isinstance(instance, Preferences):
            site_conflicts = instance.__class__.objects.filter(\
                    sites__in=instance.sites.all()).distinct()

            for conflict in site_conflicts:
                if conflict != instance:
                    for site in instance.sites.all():
                        conflict.sites.remove(site)
