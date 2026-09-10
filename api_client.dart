import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart';

class ApiClient {
  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? AppConfig.apiBaseUrl;
  final String baseUrl;

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }

  Future<String?> token() async => (await SharedPreferences.getInstance()).getString('access_token');
  Future<void> logout() async => (await SharedPreferences.getInstance()).remove('access_token');

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(Uri.parse('$baseUrl/api/v1/auth/login'), headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: {'username': email, 'password': password});
    if (response.statusCode != 200) throw Exception(_error(response));
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    await saveToken(data['access_token'] as String);
    return data;
  }

  Future<Map<String, dynamic>> me() async => _get('/api/v1/me');

  Future<Map<String, dynamic>> hydraulics(Map<String, dynamic> payload) async => _post('/api/v1/hydraulics/calculate', payload);
  Future<Map<String, dynamic>> cementing(Map<String, dynamic> payload) async => _post('/api/v1/cementing/design', payload);
  Future<List<dynamic>> projects() async {
    final data = await _getList('/api/v1/projects');
    return data;
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final response = await http.get(Uri.parse('$baseUrl$path'), headers: await _headers());
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_error(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path) async {
    final response = await http.get(Uri.parse('$baseUrl$path'), headers: await _headers());
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_error(response));
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> payload) async {
    final response = await http.post(Uri.parse('$baseUrl$path'), headers: {...await _headers(), 'Content-Type': 'application/json'}, body: jsonEncode(payload));
    if (response.statusCode < 200 || response.statusCode >= 300) throw Exception(_error(response));
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, String>> _headers() async {
    final t = await token();
    return t == null ? {} : {'Authorization': 'Bearer $t'};
  }

  String _error(http.Response response) {
    try {
      final body = jsonDecode(response.body);
      return body['detail']?.toString() ?? 'Request failed (${response.statusCode})';
    } catch (_) {
      return 'Request failed (${response.statusCode})';
    }
  }
}
