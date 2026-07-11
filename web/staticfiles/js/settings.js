{% extends "base/_app_shell.html" %}

{% block heading %}Settings{% endblock %}

{% block content %}
<div class="ds-page">

  <!-- Tabs -->
  <div class="ds-tabs">
    <button class="ds-tab is-active" data-tab="general">General</button>
    <button class="ds-tab" data-tab="employees">Employees</button>
    <button class="ds-tab" data-tab="backup">Backup & Restore</button>
    <button class="ds-tab" data-tab="database">Database</button>
    <button class="ds-tab" data-tab="about">About</button>
  </div>

  <div class="ds-tabPanels">

    <!-- General -->
    <section class="ds-tabPanel is-active" data-panel="general">
      <div class="ds-card ds-card--panel">
        <div class="ds-formGrid">
          <input class="ds-input" placeholder="Business Name">
          <input class="ds-input" placeholder="Commercial Registration Number">
          <input class="ds-input" placeholder="VAT Number">
          <input class="ds-input" placeholder="Address">
          <input class="ds-input" placeholder="Phone">
          <input class="ds-input" placeholder="Email">
          <input class="ds-input" placeholder="Branch">
          <input class="ds-input" placeholder="Currency">
          <input class="ds-input" placeholder="Exchange Rate">
        </div>

        <div class="ds-formActions">
          <button class="ds-btn">Apply</button>
          <button class="ds-btn ds-btn--primary">Save</button>
        </div>
      </div>
    </section>

    <!-- Employees -->
    <section class="ds-tabPanel" data-panel="employees">
      <div class="ds-card ds-card--panel">
        <div class="ds-toolbar">
          <div class="ds-toolbar__left">
            <button class="ds-btn ds-btn--primary">Add Employee</button>
            <button class="ds-btn">Edit</button>
            <button class="ds-btn ds-btn--danger">Delete</button>
          </div>
        </div>

        <table class="ds-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Admin</td>
              <td>admin@company.com</td>
              <td>Admin</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Backup -->
    <section class="ds-tabPanel" data-panel="backup">
      <div class="ds-card ds-card--panel">
        <div class="ds-toolbar">
          <button class="ds-btn">Backup Database</button>
          <button class="ds-btn">Restore Database</button>
        </div>
      </div>
    </section>

    <!-- Database -->
    <section class="ds-tabPanel" data-panel="database">
      <div class="ds-card ds-card--panel">

        <div class="ds-formGrid">
          <select class="ds-input">
            <option>PostgreSQL</option>
            <option>Neon</option>
          </select>

          <input class="ds-input" placeholder="Host">
          <input class="ds-input" placeholder="Port">
          <input class="ds-input" placeholder="Database Name">
          <input class="ds-input" placeholder="User">
          <input class="ds-input" placeholder="Password">
        </div>

        <div class="ds-toolbar">
          <button class="ds-btn">Test Connection</button>
          <button class="ds-btn">Migrate SQLite → PostgreSQL</button>
        </div>

      </div>
    </section>

    <!-- About -->
    <section class="ds-tabPanel" data-panel="about">
      <div class="ds-card ds-card--panel">
        <div class="ds-text">
          <b>DriveSphere</b><br>
          Car Rental Management System<br><br>
          Developed By:<br>
          Your Company Name<br>
          Version 1.0
        </div>
      </div>
    </section>

  </div>

</div>

<script src="/static/js/settings.js"></script>
{% endblock %}