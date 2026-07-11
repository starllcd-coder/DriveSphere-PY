{% extends "base/_app_shell.html" %}
{% block heading %}Customers{% endblock %}

{% block content %}
<div class="ds-page" id="ds-customers">

  <div class="ds-filters">
    <input class="ds-input" id="c-name" placeholder="Customer Name">
    <input class="ds-input" id="c-phone" placeholder="Phone">
    <input class="ds-input" id="c-id" placeholder="ID Number">
  </div>

  <div class="ds-toolbar">
    <div class="ds-toolbar__left">
      <button class="ds-btn">Upload ID / License</button>
      <button class="ds-btn">View ID / License</button>
    </div>
  </div>

  <div class="ds-card ds-tableWrap" id="c-tableCard">
    <table class="ds-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Phone</th>
          <th>ID Number</th>
          <th>Address</th>
        </tr>
      </thead>
      <tbody id="c-body">
        <tr><td colspan="4" class="ds-empty">Loading…</td></tr>
      </tbody>
    </table>
  </div>

  <div class="ds-toolbar">
    <div class="ds-toolbar__left">
      <button class="ds-btn ds-btn--primary">Add Customer</button>
      <button class="ds-btn">Edit Customer</button>
      <button class="ds-btn ds-btn--danger">Delete Customer</button>
    </div>
  </div>

</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/customers_live.js" defer></script>
{% endblock %}