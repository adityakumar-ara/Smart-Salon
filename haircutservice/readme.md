Bug Fix Summary:

- Fixed `/templates` lookup in `haircutservice/settings.py` by using `BASE_DIR / 'templates'`.
- Corrected `shopkeeper/urls.py` path typo from `sevices/` to `services/`.
- Fixed `shopkeeper/views.py` gallery creation logic to only create new `SalonImage` records when an image file is provided.
- Corrected a broken `SalonImage` creation call in `shopkeeper/views.py` by removing a nonexistent `gender` field.
- Updated `templates/shopkeeper/service_views.html` to use `service.name` and `service.target_gender` instead of invalid `service.service_name` and `service.gender`.

Notes:
- The `main.html` login/signup modal routes are now aligned with the account URL configuration.
- Existing template route name references remain unchanged and continue working with the fixed URL names.


 <!-- {% if user.is_authenticated == Shopkeeper %}

            <a href="#" class="btn btn-warning px-4" data-bs-toggle="modal" data-bs-target="#salonModal">Open Dukan</a> -->