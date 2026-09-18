import { useEffect, useMemo, useRef, useState } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap, useMapEvents } from 'react-leaflet';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';
import type { Area, Pollutant } from '../../types/api';
import { getAqiCategory } from '../../utils/aqi';
import { escapeHtml } from '../../utils/format';
import { isInValley, nearestStation, VALLEY_BOUNDS, VALLEY_CENTER } from '../../utils/geo';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { useToast } from '../../context/ToastContext';
import { useApp } from '../../context/AppContext';
import Icon from '../common/Icon';
import AqiIndicator from '../common/AqiIndicator';
import ReliabilityBadge from '../common/ReliabilityBadge';
import Freshness from '../common/Freshness';
import { ButtonLink } from '../common/Button';
interface Props {
  areas: Area[];
  selectedId?: string;
  onSelect?: (id: string) => void;
  metric?: 'AQI' | Pollutant;
  largeBubbles?: boolean;
  onPick?: (latitude: number, longitude: number) => void;
  picked?: [
    number,
    number
  ] | null;
  className?: string;
}
function MapBridge({ selected, onReady, onPick, reducedMotion }: {
  selected?: Area;
  onReady: (map: L.Map) => void;
  onPick?: Props['onPick'];
  reducedMotion: boolean;
}) {
  const map = useMap();
  const last = useRef<string | undefined>(selected?.id);
  useEffect(() => {
    onReady(map);
    const container = map.getContainer();
    const resize = new ResizeObserver(() => map.invalidateSize({ pan: false }));
    resize.observe(container);
    return () => { resize.disconnect(); };
  }, [map, onReady]);
  useEffect(() => {
    if (selected && last.current !== selected.id) {
      map.flyTo([selected.latitude, selected.longitude], Math.max(map.getZoom(), 12), { duration: reducedMotion ? 0 : 0.8, animate: !reducedMotion });
      last.current = selected.id;
    }
  }, [selected, map, reducedMotion]);
  useMapEvents({
    click: (event) => {
      if (onPick && isInValley(event.latlng.lat, event.latlng.lng))
        onPick(event.latlng.lat, event.latlng.lng);
    }
  });
  return null;
}
function StationMarker({ area, selected, metric, large, onSelect }: {
  area: Area;
  selected: boolean;
  metric: 'AQI' | Pollutant;
  large: boolean;
  onSelect?: Props['onSelect'];
}) {
  const { t, i18n } = useTranslation();
  const { areas } = useApp();
  const name = i18n.language === 'ne' ? area.nameNe : area.name;
  const category = getAqiCategory(area.reading?.aqi);
  const value = area.reading ? metric === 'AQI' ? area.reading.aqi : area.reading.pollutants[metric] : null;
  const nearest = !area.reading ? nearestStation(area, areas) : null;
  const icon = useMemo(() => {
    const label = category ? t(`aqi.${category.key}.short`) : t('noData');
    const color = category?.color ?? '#81908b';
    const ink = category?.ink ?? '#56645f';
    const html = large ? `<div class="station-bubble ${selected ? 'is-selected' : ''}" style="--station-color:${color};--station-ink:${ink};--station-bg:${category?.background ?? '#eef1ef'}"><div class="molecule"><i></i><i></i><i></i><i></i><i></i></div><span class="bubble-location">${escapeHtml(name)}</span><strong class="bubble-value">${escapeHtml(String(value ?? '?'))}</strong><span class="bubble-unit">${metric === 'AQI' ? 'US AQI' : escapeHtml(metric) + (metric === 'CO' ? ' mg/m\u00b3' : ' \u00b5g/m\u00b3')}</span><span class="bubble-category"><b>${category?.symbol ?? '?'}</b> ${escapeHtml(label)}</span></div>` : `<div class="station-pin ${selected ? 'is-selected' : ''}" style="--station-color:${color};--station-ink:${ink};--station-bg:${category?.background ?? '#eef1ef'}"><b>${escapeHtml(String(value ?? '?'))}</b><span>${escapeHtml(name)}</span></div>`;
    return L.divIcon({ className: 'aero-map-marker', html, iconSize: large ? [142, 158] : [46, 46], iconAnchor: large ? [71, 136] : [23, 23], popupAnchor: [0, large ? -110 : -20] });
  }, [category, i18n.language, large, metric, name, selected, t, value]);
  return <Marker position={[area.latitude, area.longitude]} icon={icon} title={`${name}: ${value ?? t('noData')} ${metric}`} keyboard eventHandlers={{ click: () => onSelect?.(area.id) }} zIndexOffset={selected ? 1000 : large ? 500 : 0}>
    <Popup maxWidth={280} minWidth={220}>
      <div className="station-popup">
        <p className="eyebrow">{t(`district.${area.district}`)}</p>
        <h3>{name}</h3>
        <AqiIndicator value={area.reading?.aqi} number />
        {area.reading ? <>
          <p className="popup-metric">
            {t('mainPollutant')}
            {" "}
            <strong>{area.reading.mainPollutant}</strong>
          </p>
          <div className="popup-weather"><Icon name="sun" size={15} />{area.reading.weather.temperature}&deg;C <Icon name="wind" size={15} />{area.reading.weather.windSpeed} km/h</div>
          <ReliabilityBadge reliability={area.reading.reliability} isDemo={area.reading.isDemo} />
          <Freshness date={area.reading.observedAt} isDemo={area.reading.isDemo} />
        </> : <>
          <p>{t('noStationHelp')}</p>
          {nearest && <p>{t('nearestStation')}: <strong>{nearest.area.name}</strong> ({nearest.distance.toFixed(1)} km)</p>}
        </>}
        <ButtonLink to={`/areas/${area.id}`} variant="secondary">
          {t('viewArea')}
          <Icon name="arrow-up-right" size={15} />
        </ButtonLink>
      </div>
    </Popup>
  </Marker>;
}
export default function AirMap({ areas, selectedId, onSelect, metric = 'AQI', largeBubbles = true, onPick, picked, className = '' }: Props) {
  const { t } = useTranslation();
  const toast = useToast();
  const reducedMotion = useReducedMotion();
  const [map, setMap] = useState<L.Map | null>(null);
  const [tileKey, setTileKey] = useState(0);
  const [tilesReady, setTilesReady] = useState(false);
  const [tilesFailed, setTilesFailed] = useState(false);
  const [locating, setLocating] = useState(false);
  const [position, setPosition] = useState<[
    number,
    number
  ] | null>(null);
  const failures = useRef(0);
  const selected = areas.find((area) => area.id === selectedId);
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!tilesReady)
        setTilesFailed(true);
    }, 10000);
    return () => clearTimeout(timer);
  }, [tilesReady, tileKey]);
  const recenter = () => map?.flyTo(VALLEY_CENTER, window.innerWidth < 700 ? 10.8 : 12.2, { animate: !reducedMotion, duration: 0.7 });
  const locate = () => {
    if (!navigator.geolocation) {
      toast(t('locationUnsupported'), 'error');
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      setLocating(false);
      if (!isInValley(coords.latitude, coords.longitude)) {
        toast(t('outsideValley'), 'info');
        return;
      }
      const point: [
        number,
        number
      ] = [coords.latitude, coords.longitude];
      setPosition(point);
      map?.flyTo(point, 13, { animate: !reducedMotion, duration: 0.7 });
      onPick?.(point[0], point[1]);
    }, () => { setLocating(false); toast(t('locationDenied'), 'error'); }, { timeout: 10000, maximumAge: 60000 });
  };
  return <div className={`air-map ${onPick ? 'map-picker' : ''} ${className}`} role="region" aria-label={t('mapAccessible')}>
    <div className="map-coordinate-grid" aria-hidden="true">
      <span>27.70 N / 85.35 E</span>
    </div>
    <MapContainer center={areas.length === 1 ? [areas[0].latitude, areas[0].longitude] : VALLEY_CENTER} zoom={window.innerWidth < 700 ? 10.8 : 12.2} minZoom={10} maxZoom={17} maxBounds={VALLEY_BOUNDS} maxBoundsViscosity={0.7} zoomSnap={0.2} zoomDelta={0.6} zoomControl={false} scrollWheelZoom={false} className="leaflet-map">
      <TileLayer key={tileKey} url={import.meta.env.VITE_MAP_TILE_URL || 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'} attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">CARTO</a>' eventHandlers={{
        tileload: () => { setTilesReady(true); setTilesFailed(false); }, tileerror: () => {
          failures.current += 1;
          if (failures.current > 8 && !tilesReady)
            setTilesFailed(true);
        }
      }} />
      <MapBridge selected={selected} onReady={setMap} onPick={onPick} reducedMotion={reducedMotion} />
      {areas.map((area) => <StationMarker key={area.id} area={area} selected={area.id === selectedId} metric={metric} large={largeBubbles && !!area.featured && window.innerWidth >= 700} onSelect={onSelect} />)}
      {position && <CircleMarker center={position} radius={8} pathOptions={{ fillColor: '#6550df', color: 'white', weight: 3, fillOpacity: 1 }}>
        <Popup>{t('locateMe')}</Popup>
      </CircleMarker>}
      {picked && Number.isFinite(picked[0]) && Number.isFinite(picked[1]) && <CircleMarker center={picked} radius={10} pathOptions={{ fillColor: '#6550df', color: 'white', weight: 4, fillOpacity: 1 }}>
        <Popup>{picked[0].toFixed(5)}, {picked[1].toFixed(5)}</Popup>
      </CircleMarker>}
    </MapContainer>
    <div className="map-controls">
      <button className="icon-button" onClick={() => map?.zoomIn()} aria-label={t('zoomIn')} title={t('zoomIn')}>
        <Icon name="plus" />
      </button>
      <button className="icon-button" onClick={() => map?.zoomOut()} aria-label={t('zoomOut')} title={t('zoomOut')}>
        <Icon name="minus" />
      </button>
      <span />
      <button className="icon-button" onClick={recenter} aria-label={t('recenter')} title={t('recenter')}>
        <Icon name="map" />
      </button>
      <button className="icon-button" onClick={locate} disabled={locating} aria-label={t('locateMe')} title={t('locateMe')}>{locating ? <span className="spinner spinner-small" /> : <Icon name="locate" />}</button>
    </div>
    {tilesFailed && <div className="map-offline-notice" role="status">
      <Icon name="info" size={15} />
      <span>{t('tilesUnavailable')}</span>
      <button onClick={() => { setTileKey((key) => key + 1); setTilesFailed(false); setTilesReady(false); failures.current = 0; }}>{t('retryMap')}</button>
    </div>}
  </div>;
}
