$('[id^=id_plannedWork_]').on('change', function() {
  var value = this.value;
  const last = this.id.charAt(this.id.length - 1);
  var selectedCategory = document.getElementById("id_category_" + last).value;
  var defaultCategoryElement = document.getElementById("table_" + value);
  if (defaultCategoryElement != null) {
    var defaultCategory = defaultCategoryElement.innerText;
    if (selectedCategory != parseInt(defaultCategory)) {
      categoryElement = document.getElementById("id_category_" + last)
      categoryElement.value = parseInt(defaultCategory);
    }
  } else {
    categoryElement = document.getElementById("id_category_" + last)
    categoryElement.selectedIndex = 0
  }
  
})

$('select').on('change', function() {
  categoryWarning() ;
})

$('form').submit(function(e) {
    $(':disabled').each(function(e) {
        $(this).removeAttr('disabled');
    })
});

function categoryWarning() {
    var showDisclaimer = false;
    for (let i = 0; i < 5 ; i++) {
      var element = document.getElementById("id_plannedWork_" + i );
      var categoryElement = document.getElementById("id_category_" + i);
      var value = element.value;
      if (value == "") {
          categoryElement.style.color = 'black';
      } else {
        var selectedCategory = document.getElementById("id_category_" + i).value;
        var defaultCategoryElement = document.getElementById("table_" + value);
        if (defaultCategoryElement != null) {
          var defaultCategory = defaultCategoryElement.innerText;
          if (selectedCategory == parseInt(defaultCategory)) {
            categoryElement.style.color = 'black';
          } else { 
            categoryElement.style.color = 'red';
            showDisclaimer = true;
          }
        } else {
          categoryElement.style.color = 'red';
          showDisclaimer = true;
        }
      }
    }
    if (showDisclaimer) {
      document.getElementById('disclaimerText').hidden=false;
    } else {
      document.getElementById('disclaimerText').hidden=true;
    }
}

$('.blankOffering').on('change', function() {
    let $parent = $(this).parent()
    let $clone = $parent.clone()
    let $cloneElement = $clone.children('select').eq(0)
    let name = $cloneElement.attr('name')
    let n = parseInt(name.split('_')[2]) + 1
    name = 'plannedWork_offering_' + n
    $cloneElement.val('')
    $cloneElement.attr('name', name)
    $clone.appendTo($parent.parent())
    $element = $parent.children('select').eq(0)
    $element.removeClass('blankOffering')
    $element.off('change', arguments.callee)
    $cloneElement.on('change', arguments.callee)
    $element.on('blur', hideElement) 
})

$(document).find('select[name^=plannedWork_offering_]:not(.blankOffering)').on('blur', hideElement)

function hideElement() {
    var value = $(this).val();
    if (value === ''){
        $(this).hide();
    }
}

$(window).on('load', function() {
    categoryWarning()
    $("input[type='checkbox']").each( function() {
        $(this).closest("tr").find("select[name^='offering']").prop("disabled", !this.checked)
    })
    if (document.getElementById("edit_category").value === "False"){
        for (var i = 0; i < 5; i ++) {
            document.getElementById("id_category_" + i).setAttribute("disabled", '')
        }
    }
});

$("input[type='checkbox']").on('change', function() {
    $(this).closest("tr").find("select[name^='offering']").prop("disabled", !this.checked)
});
