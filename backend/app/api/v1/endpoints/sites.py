"""
API Endpoints pour la gestion des Sites Énergétiques

Fonctionnalités :
- Lister tous les sites (avec pagination et filtres)
- Obtenir un site spécifique
- Créer un nouveau site
- Mettre à jour un site
- Supprimer un site
- Obtenir les statistiques d'un site
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.site import Site, SiteType
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse

router = APIRouter()


@router.get("/", response_model=List[SiteResponse])
def list_sites(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max d'éléments"),
    site_type: Optional[SiteType] = Query(None, description="Filtrer par type de site"),
    search: Optional[str] = Query(None, description="Recherche dans nom et location"),
    db: Session = Depends(get_db)
):
    """
    Liste tous les sites énergétiques avec pagination et filtres.
    
    **Exemples d'utilisation :**
    - GET /sites → Tous les sites (20 premiers)
    - GET /sites?limit=50 → 50 premiers sites
    - GET /sites?site_type=solar → Uniquement les parcs solaires
    - GET /sites?search=bordeaux → Sites contenant "bordeaux"
    
    **Réponse :**
    Liste de sites avec toutes leurs informations.
    """
    # Construire la requête de base
    query = db.query(Site)
    
    # Appliquer les filtres si présents
    if site_type:
        query = query.filter(Site.site_type == site_type)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Site.name.ilike(search_filter)) | 
            (Site.location.ilike(search_filter))
        )
    
    # Appliquer la pagination
    sites = query.offset(skip).limit(limit).all()
    
    return sites


@router.get("/{site_id}", response_model=SiteResponse)
def get_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un site spécifique par son ID.
    
    **Exemple :**
    GET /sites/1 → Détails du site #1
    
    **Erreurs :**
    - 404 si le site n'existe pas
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site avec l'ID {site_id} introuvable"
        )
    
    return site


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def create_site(
    site_data: SiteCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau site énergétique.
    
    **Body (JSON) :**
    ```json
    {
        "name": "Parc Solaire Bordeaux",
        "site_type": "solar",
        "location": "Bordeaux, France",
        "latitude": 44.8378,
        "longitude": -0.5792,
        "capacity_kw": 5000.0,
        "description": "Installation de 150 panneaux"
    }
    ```
    
    **Validations :**
    - Le nom doit être unique
    - La capacité doit être > 0
    - Les coordonnées GPS doivent être valides
    
    **Erreurs :**
    - 400 si le nom existe déjà
    - 422 si les données sont invalides
    """
    # Vérifier si un site avec ce nom existe déjà
    existing_site = db.query(Site).filter(Site.name == site_data.name).first()
    if existing_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un site nommé '{site_data.name}' existe déjà"
        )
    
    # Créer le nouveau site
    site = Site(**site_data.dict())
    db.add(site)
    db.commit()
    db.refresh(site)
    
    return site


@router.put("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un site existant.
    
    **Mise à jour partielle :** Seuls les champs fournis sont modifiés.
    
    **Exemple :**
    ```json
    {
        "capacity_kw": 6000.0,
        "description": "Ajout de 50 panneaux"
    }
    ```
    
    **Erreurs :**
    - 404 si le site n'existe pas
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site avec l'ID {site_id} introuvable"
        )
    
    # Mettre à jour uniquement les champs fournis
    update_data = site_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)
    
    db.commit()
    db.refresh(site)
    
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un site et tous ses compteurs/lectures associés.
    
    ⚠️ **Attention :** Cette action est irréversible !
    
    Grâce au CASCADE, la suppression entraîne :
    - Suppression de tous les compteurs du site
    - Suppression de toutes les lectures des compteurs
    
    **Erreurs :**
    - 404 si le site n'existe pas
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site avec l'ID {site_id} introuvable"
        )
    
    db.delete(site)
    db.commit()
    
    return None


@router.get("/{site_id}/statistics")
def get_site_statistics(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtient les statistiques d'un site.
    
    **Retourne :**
    - Nombre total de compteurs
    - Nombre de compteurs actifs
    - Capacité du site
    
    **Exemple de réponse :**
    ```json
    {
        "site_id": 1,
        "site_name": "Parc Solaire Bordeaux",
        "total_meters": 10,
        "active_meters": 8,
        "capacity_kw": 5000.0
    }
    ```
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site avec l'ID {site_id} introuvable"
        )
    
    # Calculer les statistiques
    total_meters = len(site.meters)
    active_meters = sum(1 for m in site.meters if m.is_active)
    
    return {
        "site_id": site_id,
        "site_name": site.name,
        "total_meters": total_meters,
        "active_meters": active_meters,
        "capacity_kw": site.capacity_kw
    }