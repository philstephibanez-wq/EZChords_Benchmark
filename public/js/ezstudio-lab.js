(function($){
'use strict';
const KEY='ezstudio.performanceHistory.v3', MAX=60, WINDOW=120000;
const num=v=>Number.isFinite(Number(v))?Number(v):0;
const fmt=(v,d=0)=>Number.isFinite(Number(v))?Number(v).toFixed(d):'—';
function confirmUi(msg){
 const d=$.Deferred();
 if(!$.ui||!$.ui.dialog){d.resolve(window.confirm(msg));return d.promise();}
 $('<div>').text(msg).dialog({modal:true,title:'Confirmation',resizable:false,minWidth:380,
 buttons:[
  {text:'Annuler',click:function(){d.resolve(false);$(this).dialog('close');}},
  {text:'OK',click:function(){d.resolve(true);$(this).dialog('close');}}
 ],
 close:function(){$(this).dialog('destroy').remove();if(d.state()==='pending')d.resolve(false);}
 });
 return d.promise();
}
function loadHistory(){try{const now=Date.now(),a=JSON.parse(localStorage.getItem(KEY)||'[]');return $.grep(Array.isArray(a)?a:[],r=>r&&now-num(r.t)<=WINDOW).slice(-MAX);}catch(e){console.error('EZStudio monitor history load failed',e);return[];}}
function saveHistory(a){try{const now=Date.now();localStorage.setItem(KEY,JSON.stringify($.grep(a,r=>r&&now-num(r.t)<=WINDOW).slice(-MAX)));}catch(_){}}
function scale(samples,key,g){if(key==='util'||key==='memory')return[0,100];if(key==='power')return[0,Math.max(1,num(g.power_limit_w))];if(key==='temp')return[20,100];if(key==='clock'){let m=Math.max(300,num(g.sm_clock_mhz));$.each(samples,(_,r)=>m=Math.max(m,num(r.clock)));return[0,m*1.05];}return[0,100];}
function plot($r,s,key,w,h,g){if(s.length<2){$r.find('[data-perf-line="'+key+'"],[data-perf-area="'+key+'"]').attr('points','');return;}const [lo,hi]=scale(s,key,g),span=Math.max(.0001,hi-lo),pts=$.map(s,(r,i)=>{const x=(i/(MAX-1))*w,v=Math.max(lo,Math.min(hi,num(r[key]))),y=h-2-((v-lo)/span)*(h-4);return[[x,y]];}),line=$.map(pts,p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' '),last=pts[pts.length-1][0];$r.find('[data-perf-line="'+key+'"]').attr('points',line);$r.find('[data-perf-area="'+key+'"]').attr('points','0,'+h+' '+line+' '+last.toFixed(1)+','+h);}
function initPerformance(){
 const $r=$('#ezs-performance-panel');if(!$r.length)return;const url=$r.data('telemetry-url');let samples=loadHistory(),timer=null,stopped=false;
 function rehydrate(){
  if(!samples.length)return;
  const last=samples[samples.length-1]||{};
  const g={
   utilization_percent:num(last.util),
   memory_percent:num(last.memory),
   power_w:num(last.power),
   power_limit_w:Math.max(num(last.powerLimit),num(last.power),1),
   temperature_c:num(last.temp),
   sm_clock_mhz:num(last.clock),
   memory_used_mib:Number.isFinite(Number(last.memoryUsed))?Number(last.memoryUsed):null,
   memory_total_mib:Number.isFinite(Number(last.memoryTotal))?Number(last.memoryTotal):null,
   pstate:last.pstate||'—',
   name:last.name||'NVIDIA GPU'
  };
  $r.find('[data-perf-name]').text(g.name);
  $r.find('[data-perf-util]').text(fmt(g.utilization_percent)+' %');
  $r.find('[data-perf-memory]').text(fmt(g.memory_percent)+' %');
  $r.find('[data-perf-power]').text(fmt(g.power_w,1)+' W');
  $r.find('[data-perf-temp]').text(fmt(g.temperature_c)+' °C');
  $r.find('[data-perf-clock]').text(fmt(g.sm_clock_mhz)+' MHz');
  $r.find('[data-stat-util]').text(fmt(g.utilization_percent)+' %');
  $r.find('[data-stat-power]').text(fmt(g.power_w,1)+' W');
  $r.find('[data-stat-temp]').text(fmt(g.temperature_c)+' °C');
  $r.find('[data-stat-clock]').text(fmt(g.sm_clock_mhz)+' MHz');
  $r.find('[data-stat-state]').text(g.pstate);
  $r.find('[data-perf-status]').text('Historique restauré · connexion télémétrie…');
  plot($r,samples,'util',360,120,g);
  plot($r,samples,'memory',174,62,g);
  plot($r,samples,'power',174,62,g);
  plot($r,samples,'temp',174,62,g);
  plot($r,samples,'clock',174,62,g);
 }
 function render(data){const g=data.gpu||{},mem=fmt(g.memory_used_mib)+' / '+fmt(g.memory_total_mib)+' MiB';
  $r.find('[data-perf-name]').text(g.name||'NVIDIA GPU');$r.find('[data-perf-util]').text(fmt(g.utilization_percent)+' %');$r.find('[data-perf-memory]').text(fmt(g.memory_percent)+' %');$r.find('[data-perf-memory-detail]').text(mem);
  $r.find('[data-perf-power]').text(fmt(g.power_w,1)+' W');$r.find('[data-perf-power-detail]').text('limite '+fmt(g.power_limit_w)+' W');$r.find('[data-perf-temp]').text(fmt(g.temperature_c)+' °C');$r.find('[data-perf-temp-detail]').text('20–100 °C');$r.find('[data-perf-clock]').text(fmt(g.sm_clock_mhz)+' MHz');$r.find('[data-perf-clock-detail]').text(g.pstate||'—');
  $r.find('[data-stat-util]').text(fmt(g.utilization_percent)+' %');$r.find('[data-stat-memory]').text(mem);$r.find('[data-stat-power]').text(fmt(g.power_w,1)+' / '+fmt(g.power_limit_w)+' W');$r.find('[data-stat-temp]').text(fmt(g.temperature_c)+' °C');$r.find('[data-stat-clock]').text(fmt(g.sm_clock_mhz)+' MHz');$r.find('[data-stat-state]').text(g.pstate||'—');$r.find('[data-perf-status]').text('Télémétrie active').addClass('perf-live-on');
  samples.push({
   t:Date.now(),
   util:num(g.utilization_percent),
   memory:num(g.memory_percent),
   memoryUsed:num(g.memory_used_mib),
   memoryTotal:num(g.memory_total_mib),
   power:num(g.power_w),
   powerLimit:num(g.power_limit_w),
   temp:num(g.temperature_c),
   clock:num(g.sm_clock_mhz),
   pstate:g.pstate||'—',
   name:g.name||'NVIDIA GPU'
  });samples=samples.slice(-MAX);saveHistory(samples);
  plot($r,samples,'util',360,120,g);plot($r,samples,'memory',174,62,g);plot($r,samples,'power',174,62,g);plot($r,samples,'temp',174,62,g);plot($r,samples,'clock',174,62,g);
 }
 function schedule(){if(stopped)return;clearTimeout(timer);timer=setTimeout(tick,2000);}
 function tick(){if(stopped)return;if(document.hidden){schedule();return;}$.ajax({url:url,method:'GET',dataType:'json',cache:false}).done(d=>{if(!d||!d.available){$r.find('[data-perf-status]').text('Télémétrie indisponible').removeClass('perf-live-on');return;}render(d);}).fail(x=>$r.find('[data-perf-status]').text('Télémétrie indisponible'+(x.status?' · HTTP '+x.status:'')).removeClass('perf-live-on')).always(schedule);}
 $(document).off('visibilitychange.ezs').on('visibilitychange.ezs',()=>{if(!document.hidden&&!stopped)tick();});$(window).off('pagehide.ezs').on('pagehide.ezs',()=>{stopped=true;clearTimeout(timer);});rehydrate();if(!samples.length)$r.find('[data-perf-status]').text('Connexion télémétrie…');tick();
}
function applyCatalogHtml(html){const $r=$('#catalog-live-region');if(!$r.length)return false;const nodes=$.parseHTML(String(html||''),document,true)||[],$wrap=$('<div>').append(nodes),$next=$wrap.find('#catalog-live-region').first();if(!$next.length)return false;$r.html($next.html());return true;}
function refreshCatalog(){const $r=$('#catalog-live-region');if(!$r.length)return;$.ajax({url:window.location.href,method:'GET',dataType:'html',cache:false}).done(html=>{if(applyCatalogHtml(html))scheduleCatalog();});}
function scheduleCatalog(){clearTimeout(window.ezstudioCatalogTimer);if($('#catalog-live-region [data-analysis-active="1"]').length)window.ezstudioCatalogTimer=setTimeout(refreshCatalog,2500);}
function initCatalog(){
 const ns='.ezstudioCatalog';
 $(document).off(ns);

 $(document).on('submit'+ns,'.catalog-delete-form',function(e){
  e.preventDefault();
  const form=this;
  const $form=$(form);
  const $button=$form.find('.catalog-delete-button');
  const message=$form.data('confirm')||'Confirmer la suppression ?';

  $.when(confirmUi(message)).done(function(ok){
   if(!ok)return;
   $button.prop('disabled',true).text('…').attr('title','Suppression en cours');
   form.submit();
  });
 });

 $(document).on('click'+ns,'.catalog-job-cancel',function(e){
  e.preventDefault();
  const $button=$(this);
  const jobId=parseInt($button.attr('data-job-id'),10);
  const url=$button.attr('data-job-cancel-url');

  if(!Number.isInteger(jobId)||jobId<=0||!url){
   window.alert('Annulation impossible : job ou route invalide.');
   return;
  }

  $.when(confirmUi('Annuler le job #'+jobId+' ?')).done(function(ok){
   if(!ok)return;

   const text=$button.text();
   $button.prop('disabled',true).text('…');

   $.ajax({
    url:url,
    type:'POST',
    dataType:'json',
    cache:false,
    timeout:3000
   })
   .done(function(){
    refreshCatalog();
   })
   .fail(function(xhr){
    const message=
     (xhr.responseJSON&&xhr.responseJSON.error)
     ||String(xhr.responseText||'').trim()
     ||('Annulation impossible · HTTP '+xhr.status);
    window.alert(message);
   })
   .always(function(){
    $button.prop('disabled',false).text(text);
   });
  });
 });

 scheduleCatalog();
}
$(function(){initPerformance();initCatalog();});
})(jQuery);
