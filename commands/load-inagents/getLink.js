var buildLink = (id) => {
    let request = HttpService.collectCommonRequest();
    request.facets = PageController.currentRegistry.selectedFacets
    request.sort = PageController.currentRegistry.sort;
    let link = HttpService.baseUrl + '/rest/registry/' + id + '/export?';

    if (!!request.search) {
        link += 'search=' + request.search + '&';
    }

    if (!!request.sort && request.sort.length !== 0) {
        request.sort.map(sv => (sv.property + ' ' + sv.direction).trim()).forEach(sv => {
            link += 'sort=' + sv + '&';
        });
    }

    if (!!request.facets) {
        Object.keys(request.facets).forEach(key => {
            if (request.facets[key] && request.facets[key].length) {
                request.facets[key].forEach(fv => {
                    link += `facets.${key}=${fv}&`;
                });
            }
        });
    }
    return link
}

var getId = () => [...document.body.innerHTML.matchAll(/let id = '(.+)'/g)][0][1]

var getLink = () => {
    let id

    try {
        id = getId()
    } catch (e) {
        return null
    }

    return buildLink(id)
}

getLink()