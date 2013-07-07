from django.conf.urls import patterns, include, url

urlpatterns = patterns('nspdice_probability.views',
  url(r'^$', 'probability_reference', name='ref'),
  url(r'^plot.png$', 'probability_reference_plot', name='ref-plot'),
)
