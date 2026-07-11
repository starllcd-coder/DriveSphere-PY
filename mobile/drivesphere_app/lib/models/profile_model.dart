class ProfileModel {
  final int id;
  final String username;
  final String email;
  final String firstName;
  final String lastName;
  final String fullName;
  final bool isActive;
  final bool isStaff;

  ProfileModel({
    required this.id,
    required this.username,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.isActive,
    required this.isStaff,
  });

  factory ProfileModel.fromJson(Map<String, dynamic> json) {
    return ProfileModel(
      id: json['id'] ?? 0,
      username: json['username']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      firstName: json['first_name']?.toString() ?? '',
      lastName: json['last_name']?.toString() ?? '',
      fullName: json['full_name']?.toString() ?? '',
      isActive: json['is_active'] ?? false,
      isStaff: json['is_staff'] ?? false,
    );
  }
}