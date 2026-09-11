import 'package:flutter/material.dart';
import '../services/api_client.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});
  final ApiClient api;
  @override State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int tab = 0;
  Map<String, dynamic>? user;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try { final u = await widget.api.me(); if (mounted) setState(() => user = u); }
    catch (_) {}
  }

  Future<void> _logout() async {
    await widget.api.logout();
    if (mounted) Navigator.of(context).pushNamedAndRemoveUntil('/', (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      HydraulicsPage(api: widget.api),
      CementingPage(api: widget.api),
      ProjectsPage(api: widget.api),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('PETRONEXA', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.5)),
        actions: [IconButton(onPressed: _logout, icon: const Icon(Icons.logout))],
      ),
      drawer: Drawer(
        child: ListView(padding: EdgeInsets.zero, children: [
          DrawerHeader(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.end, children: [
              Image.asset('assets/petronexa_logo.png', width: 190, fit: BoxFit.contain),
              const SizedBox(height: 8),
              Text(user?['email']?.toString() ?? '', style: const TextStyle(color: Colors.white70)),
            ]),
          ),
          _nav(Icons.water_drop, 'Hydraulics', 0),
          _nav(Icons.construction, 'Cementing', 1),
          _nav(Icons.folder, 'Projects', 2),
        ]),
      ),
      body: pages[tab],
    );
  }

  Widget _nav(IconData icon, String title, int index) => ListTile(
    leading: Icon(icon), title: Text(title),
    selected: tab == index,
    onTap: () { setState(() => tab = index); Navigator.pop(context); },
  );
}

class HydraulicsPage extends StatefulWidget {
  const HydraulicsPage({super.key, required this.api});
  final ApiClient api;
  @override State<HydraulicsPage> createState() => _HydraulicsPageState();
}

class _HydraulicsPageState extends State<HydraulicsPage> {
  final flow = TextEditingController(text: '550');
  final depth = TextEditingController(text: '10000');
  final mw = TextEditingController(text: '12.5');
  final pv = TextEditingController(text: '22');
  final yp = TextEditingController(text: '16');
  Map<String, dynamic>? result; String? error; bool loading = false;

  @override void dispose() { for (final c in [flow, depth, mw, pv, yp]) { c.dispose(); } super.dispose(); }

  Future<void> run() async {
    setState(() { loading = true; error = null; });
    try {
      final r = await widget.api.hydraulics({
        'flow_rate_gpm': double.parse(flow.text),
        'total_depth_ft': double.parse(depth.text),
        'surface_mud_weight_ppg': double.parse(mw.text),
        'plastic_viscosity_cp': double.parse(pv.text),
        'yield_point_lb_100ft2': double.parse(yp.text),
      });
      if (mounted) setState(() => result = r);
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally { if (mounted) setState(() => loading = false); }
  }

  Widget field(String label, TextEditingController c) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextField(controller: c, keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label)),
  );

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [
    const Text('Hydraulics Matrix', style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold)),
    const SizedBox(height: 6),
    const Text('Drilling hydraulics and safety diagnostics', style: TextStyle(color: Colors.white60)),
    const SizedBox(height: 20),
    field('Flow rate (GPM)', flow), field('Total depth (ft)', depth),
    field('Mud weight (ppg)', mw), field('Plastic viscosity (cP)', pv),
    field('Yield point (lb/100 ft²)', yp),
    FilledButton.icon(onPressed: loading ? null : run, icon: const Icon(Icons.calculate),
      label: Text(loading ? 'Calculating…' : 'Run calculation')),
    if (error != null) Padding(padding: const EdgeInsets.only(top: 12),
      child: Text(error!, style: const TextStyle(color: Colors.redAccent))),
    if (result != null) ...[
      const SizedBox(height: 20),
      _metric('Equivalent circulating density', result!['physics_results']?['equivalent_circulating_density_ecd_ppg'], 'ppg'),
      _metric('Standpipe pressure', result!['physics_results']?['standpipe_pressure_psi'], 'psi'),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
        crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Diagnostics', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(result!['diagnostics']?.toString() ?? 'No diagnostic flags returned.'),
        ]))),
    ],
  ]);

  Widget _metric(String label, dynamic value, String unit) => Card(
    child: ListTile(title: Text(label), trailing: Text('${value ?? '—'} $unit',
      style: const TextStyle(fontWeight: FontWeight.bold))),
  );
}

class CementingPage extends StatefulWidget {
  const CementingPage({super.key, required this.api});
  final ApiClient api;
  @override State<CementingPage> createState() => _CementingPageState();
}

class _CementingPageState extends State<CementingPage> {
  final hole = TextEditingController(text: '8.5');
  final casing = TextEditingController(text: '7.0');
  final length = TextEditingController(text: '5000');
  final wash = TextEditingController(text: '15');
  Map<String, dynamic>? result; String? error; bool loading = false;

  @override void dispose() { for (final c in [hole, casing, length, wash]) { c.dispose(); } super.dispose(); }

  Future<void> run() async {
    setState(() { loading = true; error = null; });
    try {
      final r = await widget.api.cementing({
        'hole_diameter_in': double.parse(hole.text),
        'casing_od_in': double.parse(casing.text),
        'casing_id_in': 6.276,
        'interval_length_ft': double.parse(length.text),
        'washout_factor_pct': double.parse(wash.text),
        'shoe_track_length_ft': 40.0,
        'lead_slurry_density_ppg': 12.5,
        'tail_slurry_density_ppg': 15.8,
        'spacer_density_ppg': 11.0,
        'displacement_fluid_density_ppg': 10.0,
        'tail_slurry_length_ft': 500.0,
        'bht_fahrenheit': 180.0,
      });
      if (mounted) setState(() => result = r);
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally { if (mounted) setState(() => loading = false); }
  }

  Widget f(String label, TextEditingController c) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextField(controller: c, keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label)),
  );

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [
    const Text('Primary Cementing', style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold)),
    const SizedBox(height: 6),
    const Text('Primary cement job design using the validated Python engine', style: TextStyle(color: Colors.white60)),
    const SizedBox(height: 20),
    f('Hole diameter (in)', hole), f('Casing OD (in)', casing),
    f('Interval length (ft)', length), f('Washout (%)', wash),
    FilledButton.icon(onPressed: loading ? null : run, icon: const Icon(Icons.calculate),
      label: Text(loading ? 'Designing…' : 'Design cement job')),
    if (error != null) Padding(padding: const EdgeInsets.only(top: 12),
      child: Text(error!, style: const TextStyle(color: Colors.redAccent))),
    if (result != null) ...[
      const SizedBox(height: 20),
      _metric('Lead slurry volume', result!['lead_slurry_volume_bbl'], 'bbl'),
      _metric('Tail slurry volume', result!['tail_slurry_volume_bbl'], 'bbl'),
      _metric('Recommended plug bumping pressure', result!['recommended_plug_bumping_pressure_psi'], 'psi'),
    ],
  ]);

  Widget _metric(String label, dynamic value, String unit) => Card(
    child: ListTile(title: Text(label), trailing: Text('${value ?? '—'} $unit',
      style: const TextStyle(fontWeight: FontWeight.bold))),
  );
}

class ProjectsPage extends StatefulWidget {
  const ProjectsPage({super.key, required this.api});
  final ApiClient api;
  @override State<ProjectsPage> createState() => _ProjectsPageState();
}

class _ProjectsPageState extends State<ProjectsPage> {
  late Future<List<dynamic>> future;

  @override void initState() { super.initState(); future = widget.api.projects(); }

  Future<void> refresh() async => setState(() { future = widget.api.projects(); });

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: refresh,
    child: FutureBuilder<List<dynamic>>(
      future: future,
      builder: (context, state) {
        if (state.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
        if (state.hasError) return Center(child: Padding(padding: const EdgeInsets.all(20),
          child: Text('Unable to load projects: ${state.error}')));
        final items = state.data ?? [];
        return ListView(padding: const EdgeInsets.all(18), children: [
          const Text('Projects', style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text('Saved well and field projects', style: TextStyle(color: Colors.white60)),
          const SizedBox(height: 16),
          if (items.isEmpty) const Card(child: Padding(padding: EdgeInsets.all(18),
            child: Text('No projects yet. Project creation is available through the API and will expand with the next modules.'))),
          ...items.map((p) => Card(child: ListTile(
            leading: const Icon(Icons.folder_outlined),
            title: Text(p['name']?.toString() ?? 'Untitled'),
            subtitle: Text('${p['well_name'] ?? ''} • ${p['field_name'] ?? ''}'),
          ))),
        ]);
      },
    ),
  );
}
