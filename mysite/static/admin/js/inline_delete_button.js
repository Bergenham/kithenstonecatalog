// inline_simple_controls.js
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const groups = document.querySelectorAll('.inline-group');
    if (!groups.length) return;

    groups.forEach(group => {
      // вставляем контролы только один раз
      if (group.querySelector('.inline-simple-controls')) return;

      const controls = document.createElement('div');
      controls.className = 'inline-simple-controls';
      controls.style.margin = '6px 0 10px 0';
      controls.style.display = 'flex';
      controls.style.gap = '8px';
      controls.style.alignItems = 'center';

      const selectAllBtn = document.createElement('button');
      selectAllBtn.type = 'button';
      selectAllBtn.className = 'button select-all-inlines';
      selectAllBtn.textContent = 'Выделить все изображения';

      const clearBtn = document.createElement('button');
      clearBtn.type = 'button';
      clearBtn.className = 'button clear-all-inlines';
      clearBtn.textContent = 'Снять выделение';

      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'button delete-selected-inlines';
      deleteBtn.textContent = 'Удалить выбранные изображения';

      // вспомогательные селекторы
      function getDeleteCheckboxes(container) {
        return Array.from(container.querySelectorAll("input[type='checkbox'][name$='-DELETE']"));
      }
      function getCheckedDeleteCheckboxes(container) {
        return getDeleteCheckboxes(container).filter(ch => ch.checked);
      }

      // select all
      selectAllBtn.addEventListener('click', function () {
        const boxes = getDeleteCheckboxes(group);
        boxes.forEach(ch => ch.checked = true);
        console.info('[inline_simple] selected', boxes.length);
      });

      // clear all
      clearBtn.addEventListener('click', function () {
        const boxes = getDeleteCheckboxes(group);
        boxes.forEach(ch => ch.checked = false);
        console.info('[inline_simple] cleared selection');
      });

      // build endpoint simply: try form.action or pathname and replace 'change/' -> 'delete_inline_images/'
      function buildEndpoint() {
        const form = document.querySelector('form');
        const source = (form && form.action) ? form.action : window.location.pathname;
        if (source.includes('/change/')) {
          return source.replace(/change\/?$/, 'delete_inline_images/');
        }
        // fallback: append suffix
        return source.replace(/\/$/, '') + '/delete_inline_images/';
      }

      // delete handler (no confirmation dialogs)
      deleteBtn.addEventListener('click', function () {
        const checked = getCheckedDeleteCheckboxes(group);
        if (!checked.length) {
          console.info('[inline_simple] nothing selected to delete');
          return;
        }

        // prepare lists: saved ids and unsaved rows
        const idsToDelete = [];
        const rowsToRemoveLocally = [];

        checked.forEach(ch => {
          const row = ch.closest('.inline-related') || ch.closest('tr') || ch.closest('.form-row');
          if (!row) return;
          const idInput = row.querySelector("input[type='hidden'][name$='-id']");
          if (idInput && idInput.value) {
            idsToDelete.push(idInput.value);
          } else {
            rowsToRemoveLocally.push(row);
          }
        });

        // remove local unsaved rows immediately
        rowsToRemoveLocally.forEach(r => r.remove());

        if (!idsToDelete.length) {
          console.info('[inline_simple] removed local rows only');
          return;
        }

        // attempt AJAX delete to endpoint
        const endpoint = buildEndpoint();
        const form = document.querySelector('form');
        const csrfInput = form ? form.querySelector('input[name="csrfmiddlewaretoken"]') : null;
        const csrf = csrfInput ? csrfInput.value : null;

        console.info('[inline_simple] attempting AJAX to', endpoint, 'ids', idsToDelete);

        fetch(endpoint, {
          method: 'POST',
          headers: Object.assign({
            'Content-Type': 'application/json'
          }, csrf ? {'X-CSRFToken': csrf} : {}),
          body: JSON.stringify({ image_ids: idsToDelete })
        })
        .then(resp => {
          if (!resp.ok) throw resp;
          return resp.json().catch(() => ({}));
        })
        .then(data => {
          // удаляем из DOM строки с этими id
          idsToDelete.forEach(id => {
            const selector = `input[type="hidden"][name$="-id"][value="${id}"]`;
            const idInput = document.querySelector(selector);
            if (idInput) {
              const row = idInput.closest('.inline-related') || idInput.closest('tr') || idInput.closest('.form-row');
              if (row) row.remove();
            }
          });
          console.info('[inline_simple] ajax delete success', data);
        })
        .catch(err => {
          // fallback: пометить чекбоксы -DELETE и нажать Save (если AJAX не сработал)
          console.warn('[inline_simple] ajax failed, falling back to form submit', err);
          // убедимся, что чекбоксы отмечены (они уже отмечены), затем нажмём save
          const saveBtn = document.querySelector('input[name="_save"], input[name="_continue"], input[name="_addanother"]');
          if (saveBtn) {
            // small visible feedback on button
            const oldText = deleteBtn.textContent;
            deleteBtn.textContent = 'Выполняется удаление...';
            saveBtn.click();
            setTimeout(() => deleteBtn.textContent = oldText, 2000);
          } else {
            console.error('[inline_simple] save button not found — cannot fallback submit');
          }
        });
      });

      controls.appendChild(selectAllBtn);
      controls.appendChild(clearBtn);
      controls.appendChild(deleteBtn);

      // вставляем контролы в начало группы (после заголовка, если есть)
      const header = group.querySelector('h2, h3');
      if (header && header.parentNode === group) {
        group.insertBefore(controls, header.nextSibling);
      } else {
        group.insertBefore(controls, group.firstChild);
      }
    });
  });
})();
