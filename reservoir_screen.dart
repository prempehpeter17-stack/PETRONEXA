import 'package:flutter/material.dart';
import '../services/api_client.dart';

class ReservoirScreen extends StatefulWidget {
  const ReservoirScreen({super.key, required this.api});
  final ApiClient api;
  @override State<ReservoirScreen> createState() => _ReservoirScreenState();
}

class _ReservoirScreenState extends State<ReservoirScreen> {
  final k=TextEditingController(text:'100'); final h=TextEditingController(text:'50'); final dp=TextEditingController(text:'500'); final mu=TextEditingController(text:'2'); final bo=TextEditingController(text:'1.2'); final l=TextEditingController(text:'1000');
  bool loading=false; String? error; Map<String,dynamic>? result;
  @override void dispose(){ for(final c in [k,h,dp,mu,bo,l]){c.dispose();} super.dispose();}
  Future<void> runDarcy() async { setState((){loading=true;error=null;}); try{ final r=await widget.api.reservoirDarcy({'permeability_md':double.parse(k.text),'thickness_ft':double.parse(h.text),'pressure_drop_psi':double.parse(dp.text),'viscosity_cp':double.parse(mu.text),'formation_volume_factor_rb_stb':double.parse(bo.text),'length_ft':double.parse(l.text)}); if(mounted)setState(()=>result=r); }catch(e){if(mounted)setState(()=>error=e.toString().replaceFirst('Exception: ',''));}finally{if(mounted)setState(()=>loading=false);}}
  Widget field(String label,TextEditingController c)=>Padding(padding:const EdgeInsets.only(bottom:10),child:TextField(controller:c,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:InputDecoration(labelText:label)));
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.all(18),children:[const Text('Reservoir Engineering',style:TextStyle(fontSize:25,fontWeight:FontWeight.bold)),const SizedBox(height:6),const Text('Reservoir properties, Darcy flow, radial flow, material balance and IPR are being connected through the same API.',style:TextStyle(color:Colors.white60)),const SizedBox(height:20),const Text('Darcy flow test',style:TextStyle(fontSize:18,fontWeight:FontWeight.bold)),field('Permeability (md)',k),field('Thickness (ft)',h),field('Pressure drop (psi)',dp),field('Viscosity (cP)',mu),field('Bo (rb/STB)',bo),field('Flow length (ft)',l)),FilledButton.icon(onPressed:loading?null:runDarcy,icon:const Icon(Icons.calculate),label:Text(loading?'Calculating…':'Calculate oil rate')),if(error!=null)Padding(padding:const EdgeInsets.only(top:10),child:Text(error!,style:const TextStyle(color:Colors.redAccent))),if(result!=null)Card(child:ListTile(title:const Text('Calculated oil rate'),trailing:Text('${(result!['oil_rate_stb_day'] as num).toStringAsFixed(2)} STB/day',style:const TextStyle(fontWeight:FontWeight.bold))))]);
}
