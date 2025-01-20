document.querySelectorAll('.modal').forEach(modal => {
    modal.setAttribute('data-bs-backdrop', 'static');
    modal.setAttribute('data-bs-keyboard', 'false');
    modal.addEventListener('submit', () => {
        modal.querySelectorAll('button').forEach(button => {
            button.disabled = true;
        });
    });
});

const newFolderModal = document.getElementById('newFolderModal');
const newFolderName = document.getElementById('newFolderName');
newFolderModal.addEventListener('shown.bs.modal', function () {
    newFolderName.focus();
});
newFolderModal.addEventListener('hidden.bs.modal', function () {
    newFolderName.value = null;
});

const renameFolderModal = document.getElementById('renameFolderModal');
const renameFolderName = document.getElementById('renameFolderName');
renameFolderModal.addEventListener('shown.bs.modal', function () {
    renameFolderName.focus();
});
renameFolderModal.addEventListener('hidden.bs.modal', function () {
    renameFolderName.value = null;
});

function setupFolder(folderId, folderName) {
    document.getElementById('renameFolderId').value = folderId;
    document.getElementById('deleteFolderId').value = folderId;

    document.getElementById('renameFolderNameDisplay').textContent = folderName;
    document.getElementById('deleteFolderNameDisplay').textContent = folderName;
}

function setupFolderMove(folderId, folderName) {
    document.getElementById('moveFolderId').value = folderId;
    document.getElementById('moveFolderNameDisplay').textContent = folderName;
    
    loadFolderTree("folder");
}

function setupFolderDetails(folderId) {
    // Show loading spinner
    document.getElementById('detailFolderLoading').classList.remove('d-none');
    document.getElementById('folderDetails').classList.add('d-none');
    
    fetch(FOLDER_DETAILS_URL, {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            folder_id: folderId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        document.getElementById('detailFolderLoading').classList.add('d-none');
        document.getElementById('folderDetails').classList.remove('d-none');
        
        document.getElementById('detailFolderName').textContent = data.name;
        document.getElementById('detailFolderCreated').textContent = data.created_at;
        document.getElementById('detailFolderUpdated').textContent = data.updated_at;
        document.getElementById('detailFolderAuthor').textContent = data.author;
        document.getElementById('detailFolderContents').textContent = 
            `${data.subfolder_count} folders, ${data.slide_count} slides`;
    })
    .catch(error => {
        console.error('Error:', error);
        document.querySelector('.folder-details').innerHTML = 
            '<div class="alert alert-danger">Error loading folder details</div>';
        document.querySelector('.folder-details').classList.remove('d-none');
        document.getElementById('detailFolderLoading').classList.add('d-none');
    });
}

const uploadSlideModal = document.getElementById('uploadSlideModal')
uploadSlideModal.addEventListener('submit', function() {        
    const selectSlide = document.getElementById('selectSlide');
    const uploadSlideLoading = document.getElementById('uploadSlideLoading');
    
    selectSlide.classList.add('d-none');
    uploadSlideLoading.classList.remove('d-none');
});
uploadSlideModal.addEventListener('hidden.bs.modal', function () {
    document.getElementById('uploadSlideName').value = null;
    document.getElementById('uploadSlideDescription').value = null;
    document.getElementById('slideFile').value = null;
});

function setupSlide(slideId, slideName) {
    document.getElementById('deleteSlideId').value = slideId;
    document.getElementById('deleteSlideNameDisplay').textContent = slideName;
}

function setupSlideEdit(slideId, slideName, slideDescription) {
    document.getElementById('editSlideId').value = slideId;
    document.getElementById('editSlideName').value = slideName;
    document.getElementById('editSlideDescription').value = slideDescription;
}

function setupSlideMove(slideId, slideName) {
    document.getElementById('moveSlideId').value = slideId;
    document.getElementById('moveSlideNameDisplay').textContent = slideName;
    
    loadFolderTree("slide");
}

function setupSlideDetails(slideId) {
    // Show loading spinner
    document.getElementById('detailSlideLoading').classList.remove('d-none');
    document.getElementById('slideDetails').classList.add('d-none');
    
    fetch(SLIDE_DETAILS_URL, {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            slide_id: slideId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        document.getElementById('detailSlideLoading').classList.add('d-none');
        document.getElementById('slideDetails').classList.remove('d-none');
        
        // Populate slide details
        document.getElementById('detailSlideName').textContent = data.name;
        document.getElementById('detailSlideDescription').textContent = data.description || '-';
        document.getElementById('detailSlideCreated').textContent = data.created_at;
        document.getElementById('detailSlideUpdated').textContent = data.updated_at;
        document.getElementById('detailSlideAuthor').textContent = data.author;
        document.getElementById('detailSlideFolder').textContent = data.folder;
        document.getElementById('detailSlideFile').textContent = data.file;

        const metadataElement = document.getElementById('detailSlideMetadata');
        if (data.metadata) {
            try {
                // If metadata is a string, parse it; if it's already an object, use it directly
                const metadataObj = typeof data.metadata === 'string' 
                    ? JSON.parse(data.metadata) 
                    : data.metadata;
                
                // Format the metadata with proper indentation
                const formattedMetadata = JSON.stringify(metadataObj, null, 2);
                
                // Create a pre element for formatted display
                metadataElement.innerHTML = `<pre class="mb-0">${formattedMetadata}</pre>`;
            } catch (e) {
                // If parsing fails, display as is
                metadataElement.textContent = "couldn't load metadata";
            }
        } else {
            metadataElement.textContent = '-';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.querySelector('.slide-details').innerHTML = 
            '<div class="alert alert-danger">Error loading slide details</div>';
        document.querySelector('.slide-details').classList.remove('d-none');
        document.getElementById('detailSlideLoading').classList.add('d-none');
    });
}

function loadFolderTree(type) {
    const container = document.getElementById('folderTreeContainer_' + type);
    container.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Loading...';

    // Fetch folder structure from server
    fetch(FOLDER_TREE_URL)
    .then(response => response.json())
    .then(data => {
        container.innerHTML = '<ul class="list-unstyled mb-0">' 
            + (type == "folder" || !data.show_root ? '' : `<li class="mb-2">
                    <div class="form-check">
                        <input class="form-check-input folder-select" 
                        type="radio" 
                        name="destination_folder_id" 
                        id="folder_root" 
                        value="" 
                        required>
                        <label class="form-check-label" for="folder_root">
                            <i class="bi bi-folder text-warning me-2"></i> Root
                        </label>
                    </div>
                </li>`)
            + buildFolderTree(data.tree, type) + '</ul>';
    }) 
    .catch(error => {
        console.error('Error:', error);
        container.innerHTML = `<div class="text-danger">${error}</div>`;
    });
}

function buildFolderTree(folders, type) {
    let html = '';
    folders.forEach(folder => {
        folderAvailable = type == "folder" ? folder.id != document.getElementById('moveFolderId').value : true
        collapseAvailable = folder.subfolders.length && folderAvailable
        html += `
            <li class="mb-2">
                <div class="form-check">
                    <input class="form-check-input folder-select" 
                        type="radio" 
                        name="destination_folder_id" 
                        id="folder_${folder.id}" 
                        value="${folder.id}" 
                        ${folderAvailable ? '' : 'disabled'} required>
                    <label class="form-check-label" for="folder_${folder.id}">
                        <i class="bi bi-folder text-warning me-2"></i> ${folder.name}
                    </label>
                    <i class="bi bi-chevron-down" data-bs-toggle="collapse" href="#collapse_${folder.id}" role="button" ${collapseAvailable ? '' : 'hidden'}></i>
                </div>
                <ul class="list-unstyled mb-0 collapse" id="collapse_${folder.id}">
                    ${collapseAvailable ? buildFolderTree(folder.subfolders, type) : ''}
                </ul>
            </li>`;
    });
    return html;
}