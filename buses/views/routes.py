from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from ..models import Route, RouteStop, RouteSegment
from ..forms import RouteForm, RouteStopForm, RouteSegmentForm
from helpers.mixins import UIDObjectMixin


# ════════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════════

class RouteListView(LoginRequiredMixin, ListView):
    """List all routes"""
    model = Route
    template_name = 'routes/index.html'
    context_object_name = 'routes'
    paginate_by = 20

    def get_queryset(self):
        queryset = Route.objects.filter(is_reverse=False).prefetch_related('stops', 'segments', 'schedules')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(schedules__isnull=False).distinct()
        elif status == 'inactive':
            queryset = queryset.filter(schedules__isnull=True).distinct()
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_routes'] = Route.objects.filter(is_reverse=False).count()
        context['active_routes'] = Route.objects.filter(is_reverse=False, schedules__isnull=False).distinct().count()
        context['inactive_routes'] = Route.objects.filter(is_reverse=False, schedules__isnull=True).distinct().count()
        return context


class RouteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new route"""
    model = Route
    form_class = RouteForm
    template_name = 'routes/create.html'
    success_message = "Route '%(name)s' created successfully"

    def form_valid(self, form):
        # Ensure is_reverse is False
        form.instance.is_reverse = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('routes-detail', kwargs={'uid': self.object.uid})


class RouteDetailView(LoginRequiredMixin, UIDObjectMixin, DetailView):
    """Display route details with stops, segments, and reverse route"""
    model = Route
    template_name = 'routes/detail.html'
    context_object_name = 'route'

    def get_queryset(self):
        return Route.objects.filter(is_reverse=False).prefetch_related('stops', 'segments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route = self.object
        
        context['form'] = RouteForm(instance=route)
        context['stops'] = route.stops.all().order_by('order')
        context['segments'] = route.segments.all().select_related('from_stop', 'to_stop')
        context['stop_form'] = RouteStopForm()
        context['segment_form'] = RouteSegmentForm(route=route)
        context['schedules'] = route.schedules.all().select_related('bus').order_by('-departure_time')[:10]
        
        # Reverse route info
        context['reverse_route'] = route.reverse_route if hasattr(route, 'reverse_route') else None
        if context['reverse_route']:
            context['reverse_stops'] = context['reverse_route'].stops.all().order_by('order')
            context['reverse_segments'] = context['reverse_route'].segments.all().select_related('from_stop', 'to_stop')
        
        return context


class RouteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UIDObjectMixin, UpdateView):
    """Update route information"""
    model = Route
    form_class = RouteForm
    template_name = 'routes/update.html'
    success_message = "Route updated successfully"

    def get_queryset(self):
        return Route.objects.filter(is_reverse=False)

    def get_success_url(self):
        return reverse_lazy('routes-detail', kwargs={'uid': self.object.uid})


class RouteDeleteView(LoginRequiredMixin, UIDObjectMixin, DeleteView):
    """Delete route"""
    model = Route
    template_name = 'routes/delete.html'
    success_url = reverse_lazy('routes-index')

    def get_queryset(self):
        return Route.objects.filter(is_reverse=False)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        route_name = self.object.name
        response = super().delete(request, *args, **kwargs)
        # Delete reverse route too
        if self.object.reverse_route:
            self.object.reverse_route.delete()
        return response


class RouteDeleteReverseView(LoginRequiredMixin, UIDObjectMixin, View):
    """Delete reverse route"""
    model = Route

    def post(self, request, uid):
        route = get_object_or_404(Route, uid=uid, is_reverse=False)
        
        if route.reverse_route:
            route.reverse_route.delete()
            message = f"Reverse route for '{route.name}' deleted"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': message})
        
        return redirect('routes-detail', uid=route.uid)


# ════════════════════════════════════════════════════════════════
# ROUTE STOPS
# ════════════════════════════════════════════════════════════════

class RouteStopCreateView(LoginRequiredMixin, UIDObjectMixin, View):
    """Create a route stop via AJAX"""
    model = Route

    def post(self, request, uid):
        route = get_object_or_404(Route, uid=uid, is_reverse=False)
        form = RouteStopForm(request.POST)
        
        if form.is_valid():
            stop = form.save(commit=False)
            stop.route = route
            stop.save()
            
            return JsonResponse({
                'success': True,
                'stop': {
                    'uid': str(stop.uid),
                    'name': stop.name,
                    'order': stop.order,
                }
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class RouteStopUpdateView(LoginRequiredMixin, UIDObjectMixin, View):
    """Update a route stop via AJAX"""
    model = RouteStop

    def post(self, request, uid):
        stop = get_object_or_404(RouteStop, uid=uid)
        form = RouteStopForm(request.POST, instance=stop)
        
        if form.is_valid():
            stop = form.save()
            
            return JsonResponse({
                'success': True,
                'stop': {
                    'uid': str(stop.uid),
                    'name': stop.name,
                    'order': stop.order,
                }
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class RouteStopDeleteView(LoginRequiredMixin, UIDObjectMixin, View):
    """Delete a route stop via AJAX"""
    model = RouteStop

    def post(self, request, uid):
        stop = get_object_or_404(RouteStop, uid=uid)
        route_uid = stop.route.uid
        stop.delete()
        
        return JsonResponse({
            'success': True,
            'message': f"Stop '{stop.name}' deleted"
        })


class RouteStopReorderView(LoginRequiredMixin, UIDObjectMixin, View):
    """Reorder route stops via drag-drop (AJAX)"""
    model = Route

    def post(self, request, uid):
        route = get_object_or_404(Route, uid=uid, is_reverse=False)
        stops = request.POST.getlist('stops[]')
        
        try:
            for index, stop_uid in enumerate(stops, 1):
                RouteStop.objects.filter(uid=stop_uid, route=route).update(order=index)
            
            return JsonResponse({
                'success': True,
                'message': 'Stops reordered successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ════════════════════════════════════════════════════════════════
# ROUTE SEGMENTS
# ════════════════════════════════════════════════════════════════

class RouteSegmentCreateView(LoginRequiredMixin, UIDObjectMixin, View):
    """Create a route segment via AJAX"""
    model = Route

    def post(self, request, uid):
        route = get_object_or_404(Route, uid=uid, is_reverse=False)
        form = RouteSegmentForm(request.POST, route=route)
        
        if form.is_valid():
            segment = form.save(commit=False)
            segment.route = route
            segment.save()
            
            return JsonResponse({
                'success': True,
                'segment': {
                    'uid': str(segment.uid),
                    'from_stop': segment.from_stop.name,
                    'to_stop': segment.to_stop.name,
                    'price': float(segment.price),
                }
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class RouteSegmentUpdateView(LoginRequiredMixin, UIDObjectMixin, View):
    """Update a route segment via AJAX"""
    model = RouteSegment

    def post(self, request, uid):
        segment = get_object_or_404(RouteSegment, uid=uid)
        form = RouteSegmentForm(request.POST, instance=segment, route=segment.route)
        
        if form.is_valid():
            segment = form.save()
            
            return JsonResponse({
                'success': True,
                'segment': {
                    'uid': str(segment.uid),
                    'from_stop': segment.from_stop.name,
                    'to_stop': segment.to_stop.name,
                    'price': float(segment.price),
                }
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class RouteSegmentDeleteView(LoginRequiredMixin, UIDObjectMixin, View):
    """Delete a route segment via AJAX"""
    model = RouteSegment

    def post(self, request, uid):
        segment = get_object_or_404(RouteSegment, uid=uid)
        segment.delete()
        
        return JsonResponse({
            'success': True,
            'message': f"Segment deleted"
        })