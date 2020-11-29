from app.googleplanten import GooglePlanten
import sys
import time

def merge_plantenfiches(lijst_planten, delete_old = True):
    aantal_fiches = 0

    if lijst_planten and len(lijst_planten) > 0:
        plantenstats, planttabel, aantal_planten = get_planttabel()

        if aantal_planten > 0:
            planten = GooglePlanten()

            #planten.update_sheet_last_editor()

            # Delete old
            if delete_old:
                planten.delete_fiches()

            # Create new
            for plant in planttabel:
            
                if str(plant.get('id')) in lijst_planten:
                    print('Plant %s %s' % (plant.get('id'), plant.get('plantnaamnl')))
                    merged_document_id = planten.merge_template(plant, planten.DOCS_FILE_ID, planten.SOURCE, planten.DRIVE, plant.get("plantnaamnl"))

                    aantal_fiches = aantal_fiches + 1

                    if plant.get("foto"):
                        if ',' in plant.get("foto"):
                            foto_array = plant.get("foto").split(",")
                        else:
                            foto_array=[ plant.get("foto") ]

                        indexpos = False
                        for f in foto_array:
                            image = f
                            print("Change perm: %s" % (image))
                            planten.set_permissions_image(image)
                            
                        time.sleep(2)
                        for f in foto_array:
                            image = f 
                            # Lookup the indexid in the document
                            if not indexpos:
                                indexpos = planten.get_placeholder_image_index(merged_document_id, image)
                            else:
                                indexpos += 1
                            if indexpos:
                                # Replace the image
                                #print("1/--- Indexpos: %s Document: %s Image: %s" % (indexpos, merged_document_id, image))
                                #planten.set_permissions_image(image)
                                
                                image_uc = image.replace("open?id=","uc?id=")
                                print("2/--- Indexpos: %s Document: %s Image: %s Image_uc: %s" % (indexpos, merged_document_id, image, image_uc))
                                planten.replace_placeholder_image(merged_document_id, image, image_uc, indexpos)
    
    if aantal_fiches > 0:
        return True, aantal_fiches
    else:
        return False, aantal_fiches


def get_planttabel(formfilter = False):
    planten = GooglePlanten()
    planttabel = planten.get_sheets_data()

    result_planttabel = []

    if formfilter: 
        filtersoortplant = formfilter[0]['soortplant'].lower().strip()
        filterbloei = list(map(str.lower,formfilter[0]['bloei']))        
        filterbodemvereisten = list(map(str.lower,formfilter[0]['bodemvereisten']))
        filterzonschaduw = list(map(str.lower,formfilter[0]['zonschaduw']))

        rules = [ 
            len(filtersoortplant) > 0,
            len(filterbloei) > 0,
            len(filterbodemvereisten) > 0,
            len(filterzonschaduw) > 0,
        ]

        if any(rules):
            for plant in planttabel:

                # Check soort
                if plant['soortplant'].lower().strip() in filtersoortplant:
                    result_planttabel.append(plant)
                    continue

                # Check bloei
                continue_plantbloei = False
                for plantbloei in plant['bloei'].split(','):
                    if plantbloei.lower().strip() in filterbloei:
                        result_planttabel.append(plant)
                        continue_plantbloei = True
                        break
                if continue_plantbloei:
                    continue
                    
                # Check bodem
                continue_plantbodem = False
                for plantbodem in plant['bodemvereisten'].split(','):
                    if plantbodem.lower().strip() in filterbodemvereisten:
                        result_planttabel.append(plant)
                        continue_plantbodem = True
                        break
                if continue_plantbodem:
                    continue                    

                # Check zon
                continue_plantzon = False
                for plantzon in plant['zonschaduw'].split(','):
                    if plantzon.lower().strip() in filterzonschaduw:
                        result_planttabel.append(plant)
                        continue_plantzon = True
                        break
                if continue_plantzon:
                    continue      


            planttabel = result_planttabel

    aantal_planten = len(planttabel)
    stats = [0,0,0]

    return stats, planttabel, aantal_planten